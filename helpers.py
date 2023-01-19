import random
import string

def genCode():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(6))