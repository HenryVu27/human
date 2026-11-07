from humanizer.pipeline.copypen import CopyPenalty


class WordTok:
    """Toy tokenizer: one token per space-led word, so spans count words."""

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.inv: dict[int, str] = {}

    def _id(self, w):
        if w not in self.vocab:
            self.vocab[w] = len(self.vocab)
            self.inv[self.vocab[w]] = w
        return self.vocab[w]

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [self._id(" " + w) for w in text.split()]}

    def decode(self, ids):
        return "".join(self.inv[i] for i in ids)


def test_penalizes_the_token_that_completes_a_copied_run():
    tok = WordTok()
    src = "the model learns to copy whole runs of the draft verbatim"
    pen = CopyPenalty(tok, src, strength=2.0, span=4)
    gen = tok("so the model learns")["input_ids"]
    assert pen.penalized(gen) == {tok("to")["input_ids"][0]}
    assert pen.penalized(tok("so the model forgets")["input_ids"]) == set()


def test_names_numbers_and_quotes_are_exempt():
    tok = WordTok()
    src = 'we met with Ada Lovelace in 1843 and she said "the engine weaves algebraic patterns" to us'
    pen = CopyPenalty(tok, src, strength=2.0, span=3)
    assert pen.penalized(tok("met with Ada")["input_ids"][:2]) == set()          # completing token "Ada" is a name
    assert pen.penalized(tok("Lovelace in")["input_ids"]) == set()                # completing token "1843"
    assert pen.penalized(tok('"the engine')["input_ids"]) == set()               # inside the input's quote


def test_strength_zero_is_off():
    tok = WordTok()
    pen = CopyPenalty(tok, "a b c d e", strength=0.0, span=3)
    assert pen.penalized(tok("a b")["input_ids"]) == set()
