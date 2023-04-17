WORDS = []
with open("words.txt", "r") as f:
    WORDS = f.read().lower().split("\n")

def isWord(word):
    if word is None:
        return

    word = word.lower()

    return word in WORDS