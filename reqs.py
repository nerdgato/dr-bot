import os

def generate_requirements():
    os.system("pip install pipreqs")
    os.system("pipreqs . --force")

if __name__ == "__main__":
    generate_requirements()