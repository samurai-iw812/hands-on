#!/usr/bin/env python3
# decode_sct_full.py
# استخدام:
#   python3 decode_sct_full.py          -> يلصق النص يدوياً من stdin ثم Enter+Ctrl-D
#   python3 decode_sct_full.py file.txt -> يقرأ النص من الملف (مثالي لو لديك joined string محفوظ)

import sys, re, base64, zlib, argparse, os

def try_b64_decode(s):
    try:
        return base64.b64decode(s, validate=True)
    except Exception:
        # محاولة أقل تشددًا (بعض النصوص قد لا تكون "strict")
        try:
            return base64.b64decode(s)
        except Exception:
            return None

def extract_joined(raw):
    # نحتفظ فقط بأحرف Base64 (A-Za-z0-9+/=)
    chars = re.findall(r"[A-Za-z0-9+/=]", raw)
    return "".join(chars)

def detect_and_print_text(bbytes, label):
    # نحاول أن نفسّر البايتس بعدة encoding شائعة
    results = {}
    try:
        txt = bbytes.decode("utf-16le")
        results['utf-16le'] = txt
    except Exception:
        pass
    try:
        txt = bbytes.decode("utf-8", errors="replace")
        results['utf-8'] = txt
    except Exception:
        pass
    try:
        txt = bbytes.decode("latin1")
        results['latin1'] = txt
    except Exception:
        pass

    if not results:
        print(f"[!] {label}: لم أتمكن من تحويل البايتس إلى نص معروف. عرض أول 200 بايت:")
        print(bbytes[:200])
        return None

    # نطبع الأنسب: نفضل utf-16le إن وجد (PowerShell عادة يكون UTF-16LE)
    preferred = None
    if 'utf-16le' in results:
        preferred = ('utf-16le', results['utf-16le'])
    elif 'utf-8' in results:
        preferred = ('utf-8', results['utf-8'])
    else:
        preferred = next(iter(results.items()))

    enc, text = preferred
    print(f"\n=== {label} (interpreted as {enc}) ===\n")
    print(text)
    return text

def find_and_decode_inner_b64s(text, outdir):
    # نبحث عن سلاسل Base64 محتملة داخل النص (طولها >= 8)
    candidates = re.findall(r"[A-Za-z0-9+/=]{8,400}", text)
    candidates = list(dict.fromkeys(candidates))  # unique preserving order
    results = []
    if not candidates:
        print("\n[!] لا توجد سلاسل Base64 داخل النص.")
        return results

    print(f"\n[+] Found {len(candidates)} Base64 candidate(s). Decoding each (showing best interpretation):\n")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "b64_candidates.txt"), "w", encoding="utf-8", errors="ignore") as f:
        for i,cand in enumerate(candidates, 1):
            b = try_b64_decode(cand)
            if b is None:
                print(f"[{i}] Candidate NOT base64: {cand[:80]}{'...' if len(cand)>80 else ''}")
                f.write(f"[{i}] NOT base64: {cand}\n\n")
                continue
            # attempt encodings
            decoded_text = None
            for enc in ("utf-8","utf-16le","latin1"):
                try:
                    s = b.decode(enc, errors="ignore")
                    if len(s.strip())>0 and any(ch.isalpha() for ch in s):
                        decoded_text = (enc, s)
                        break
                except Exception:
                    pass
            if decoded_text is None:
                # store raw bytes hex as fallback
                hexpreview = b[:200].hex()
                print(f"[{i}] Decoded bytes (no clear text). len={len(b)} bytes. Hex preview: {hexpreview[:120]}...")
                f.write(f"[{i}] bytes len={len(b)}\nhex:{hexpreview}\n\n")
                results.append((cand, b, None))
            else:
                enc, s = decoded_text
                print(f"[{i}] Candidate OK (as {enc}), bytes len={len(b)}")
                # print small preview
                preview = s.strip()[:1000]
                print(preview)
                f.write(f"[{i}] candidate: {cand}\ninterpreted as {enc} (len {len(b)} bytes):\n{preview}\n\n")
                results.append((cand, b, (enc, s)))
    return results

def search_flags(all_text):
    # البحث عن FLAG{...} أو flag{...} أو كلمات مفتاح
    flags = re.findall(r"(FLAG\{.*?\}|flag\{.*?\})", all_text, flags=re.DOTALL)
    if flags:
        print("\n*** FOUND FLAG(s):")
        for fl in flags:
            print(fl)
    else:
        # بحث عن كلمات أخرى مفيدة: "password", "key", "http", "https"
        hints = re.findall(r"(password|passwd|key|secret|http[s]?://[^\s'\"<>]+)", all_text, flags=re.IGNORECASE)
        if hints:
            print("\n[!] لم أعثر على FLAG مباشرة، لكن وُجدت دلائل/روابط/مفاتيح محتمله:")
            for h in hints[:50]:
                print(" -", h)
        else:
            print("\n[!] لا FLAG واضح ولا كلمات مفتاحية عُثر عليها في هذا النص.")

def main():
    parser = argparse.ArgumentParser(description="Decode obfuscated .sct 'effected' string (remove noise, base64 decode, find inner base64s).")
    parser.add_argument("file", nargs="?", help="File containing the raw var effected = \"...\" text (or paste via stdin).")
    parser.add_argument("--outdir", default="decode_output", help="Directory to save outputs")
    args = parser.parse_args()

    if args.file:
        raw = open(args.file, "r", encoding="utf-8", errors="ignore").read()
    else:
        print("الصق النص الكامل هنا (أو أرسل EOF (Ctrl-D) عند الانتهاء):")
        raw = sys.stdin.read()

    joined = extract_joined(raw)
    if not joined:
        print("[!] لم يتم استخراج أي حروف Base64 من النص. تأكد أنك نقلت النص الصحيح.")
        return

    print("[*] Stage1: extracted joined string (أول 200 chars):")
    print(joined[:200] + ("..." if len(joined)>200 else ""))

    # Attempt primary Base64 decode
    b = try_b64_decode(joined)
    if b is None:
        print("\n[!] joined string ليس Base64 صالح أو مفقود padding.")
        # Still try to heuristically break into chunks and decode candidates from joined
        # We'll search for candidate substrings inside joined (>=16 chars)
        cand_subs = re.findall(r"[A-Za-z0-9+/=]{16,400}", joined)
        if not cand_subs:
            print("[!] لا substrings للـBase64 واصل للحل.")
            return
        print(f"[!] وجد {len(cand_subs)} candidate substrings داخل joined. سنجرب decode كل واحد...")
        all_text = ""
        for idx, csub in enumerate(cand_subs, 1):
            bb = try_b64_decode(csub)
            if bb:
                t = detect_and_print_text(bb, f"candidate#{idx}")
                if t:
                    all_text += "\n" + t
        if all_text:
            search_flags(all_text)
        return

    # If we got bytes, try to interpret as UTF-16LE (common for PowerShell)
    main_text = None
    try:
        main_text = b.decode("utf-16le")
    except Exception:
        try:
            main_text = b.decode("utf-8", errors="ignore")
        except Exception:
            main_text = None

    # print best interpretation
    if main_text:
        print("\n[+] Primary Base64 decoded -> text (preview):\n")
        print(main_text[:1500])
        # save main text
        os.makedirs(args.outdir, exist_ok=True)
        with open(os.path.join(args.outdir, "decoded_main.txt"), "w", encoding="utf-8", errors="ignore") as f:
            f.write(main_text)
    else:
        print("[!] نجح فك Base64 لكن لم أتمكن من تحويله لنص معروف. حفظت البايتس كـ decoded_main.bin")
        os.makedirs(args.outdir, exist_ok=True)
        with open(os.path.join(args.outdir, "decoded_main.bin"), "wb") as f:
            f.write(b)

    # بحث عن المزيد من Base64 بداخل النص وفكها
    inner_results = []
    if main_text:
        inner_results = find_and_decode_inner_b64s(main_text, args.outdir)

    # اجمع النصوص كلها للبحث عن FLAG
    combined_text = main_text or ""
    for cand, bbytes, decinfo in inner_results:
        if decinfo and decinfo[1]:
            combined_text += "\n" + decinfo[1]

    search_flags(combined_text)

    print(f"\n[+] نتائج محفوظة في المجلد: {args.outdir}")

if __name__ == "__main__":
    main()
