import random


def create_otp(length:int=4):
    return ''.join(random.choices('0123456789', k=length))


