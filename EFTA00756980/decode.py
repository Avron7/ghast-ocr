import base64

if __name__ == "__main__":
    # first base64 portion is a plaintext email thread
    with open(f"output/raw1.txt") as f:
        full_text = "".join(l.rstrip() for l in f.readlines())

    decoded = base64.b64decode(full_text)

    with open(f'output/message.txt', 'wb') as output_file:
        output_file.write(decoded)
    print(f"Wrote: 'output/message.txt'")

    # 2nd base64 portion is the same thread formatted as html
    with open(f"output/raw2.txt") as f:
        full_text = "".join(l.rstrip() for l in f.readlines())

    decoded = base64.b64decode(full_text)

    with open(f'output/message.html', 'wb') as output_file:
        output_file.write(decoded)
    print(f"Wrote: 'output/message.html'")
