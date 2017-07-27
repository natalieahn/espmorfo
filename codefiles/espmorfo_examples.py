# ESPMORFO
# Example code for using the classes in espmorfo.py
# -----------------------------------------------------------------------------

import re
from espmorfo import EspMorfoWordLabeler

wordlabeler = EspMorfoWordLabeler()
text = 'Ésta frase sirve como ejemplo para familiarizarnos con ' \
     + 'las herramientas técnicas de espmorfo .'

# Split contractions in tokenized text:
text_noclitics = wordlabeler.split_contractions(text)
toks = text_noclitics.split()

# Extract word features from raw tokens alone:
tok_feats = [wordlabeler.extract_word_features(tok) for tok in toks]
print([(toks[i], tok_feats[i]['gender']) for i in range(len(toks))])
print([(toks[i], tok_feats[i]['number']) for i in range(len(toks))])

# Extract word features from part-of-speech tagged tokens:
toks_tags = [('Ésta','DT'), ('frase','NN'), ('sirve','VB'),
			 ('como','IN'), ('ejemplo','NN'), ('para','IN'),
			 ('nos','PRP'), ('familiarizar','VB'), ('con','IN'),
			 ('las','DT'), ('herramientas','NNS'), ('computacionales','JJS'),
			 ('de','IN'), ('espmorfo','NNP'), ('.','.')]
tok_feats = [wordlabeler.extract_word_features(tok, tag[0]) \
			 for (tok, tag) in toks_tags]
for i in range(len(toks_tags)):
	if re.match('[NJ]', toks_tags[i][1]):
		print('%20s: %s, %s %s' % (toks_tags[i][0], toks_tags[i][1],
			tok_feats[i]['number'], tok_feats[i]['gender']))
	elif re.match('V', toks_tags[i][1]):
		print('%20s: %s, %s %s %s' % (toks_tags[i][0], toks_tags[i][1],
			tok_feats[i]['tense'], tok_feats[i]['mood'], tok_feats[i]['person']))
	else: print('%20s: %s' % (toks_tags[i][0], toks_tags[i][1]))

# Lemmatize word forms:
tok_lems = [wordlabeler.lemmatize(tok, tag[0]) for (tok, tag) in toks_tags]
for i in range(len(toks_tags)):
	if re.match('V|.+S$', toks_tags[i][1]):
		print('token: %s, lemma: %s' % (toks_tags[i][0], tok_lems[i]))

# Nominalize verbs:
print(wordlabeler.nominalize('familiarizar'))
