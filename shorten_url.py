import random,string
def shorten_url(length_url):
    try:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length_url))
    except Exception as e:
        print(e)