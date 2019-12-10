import os
import re
from .save_utils import save_obj, load_obj


_PATH_FILE = os.path.dirname(__file__)
_get_abs_path = lambda path: os.path.normpath(os.path.join(_PATH_FILE, path))

DEFAULT_TFIDF = None
DEFAULT_TFIDF_NAME = "tfidf.pkl"


class NaiEnDetector:
    def __init__(self):
        self.DEFAULT_TFIDF_NAME = DEFAULT_TFIDF_NAME
        self.tfidf = load_obj(_get_abs_path(DEFAULT_TFIDF_NAME))


    def predict_line(self, line):
        tokens = re.findall('[\w\-\']+', line.lower())
        line_prob_en = 1
        line_prob_pcm = 1
        for n in range(len(tokens)):
            if n == 0:
                pass
            else:
                bigram = '{}@&{}'.format(tokens[n-1], tokens[n])
                p_en = self.tfidf['en'].get(bigram, None)
                p_pcm = self.tfidf['pcm'].get(bigram, None)
                if (p_en == None) & (p_pcm == None):
                    continue
                elif (p_en == None):
                    p_en = 1 - p_pcm + 0.0001
                elif (p_pcm == None):
                    p_pcm = 1 - p_en + 0.0001
                line_prob_en *= p_en
                line_prob_pcm *= p_pcm
        if (line_prob_en == 1) & (line_prob_pcm == 1):
            label = 'unknown'
        elif line_prob_en >= line_prob_pcm:
            label = 'en'
        elif line_prob_en < line_prob_pcm:
            label = 'pcm'

        return label


