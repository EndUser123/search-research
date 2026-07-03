import os

with open("P:/test_seek.txt", "wb") as f:
    f.write(b"hello")

with open("P:/test_seek.txt", "rb") as f:
    try:
        f.seek(-10, 2)
        print("seek success:", f.read())
    except Exception as e:
        print("seek failed:", repr(e))
