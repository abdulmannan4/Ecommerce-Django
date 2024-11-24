from django.core.cache import cache
import random
def send_otp_to_mobile(mobile, user_obj):
    try:
        if cache.get(mobile):
            return False, None

        otp_to_send = random.randint(1000, 9999)
        cache.set(mobile, otp_to_send, timeout=60)

        user_obj.otp = otp_to_send
        user_obj.save()

        return True, None
    except Exception as e:
        print(e)
        return False, e
