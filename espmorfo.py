# ESPMORFO
# Classes and methods for morphological analysis of Spanish text.
# -----------------------------------------------------------------------------
# Copyright 2017 Natalie Ahn
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details, <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# Lexical and morphological rules in the accompanying files are derived from
# the following project, distributed under the same GNU GPL license:
#
# Santiago Rodríguez and Jesús Carretero. 1996.
# "A Formal Approach to Spanish Morphology: The COES Tools."
# Procesamiento del Lenguaje Natural, 19 September 1996.
# http://www.datsi.fi.upm.es/~coes/coes.html
# -----------------------------------------------------------------------------

import re
import xlrd
from bisect import bisect_left

default_rules_dir = './rulefiles/'

class EspMorfoWordLabeler:
	root_flags = {}
	root_list = []
	morph_rules = {}
	nom_forms = {}
	contractions = {}
	word_feats = {}
	word_lemmas = {}
	entity_tree = ['root',[]]

	def __init__(self, vocab_file=default_rules_dir+'espmorfo_words.txt',
				 rule_file=default_rules_dir+'espmorfo_rules.xlsx'):
		self._read_in_vocab(vocab_file)
		self._read_in_rules(rule_file)
		self._read_in_pronouns(rule_file)
		self._read_in_contractions(rule_file)
		self._read_in_entities(rule_file)

	def _read_in_vocab(self, vocab_file):
		with open(vocab_file, 'r') as f:
			for line in f:
				parts = self._convert_spec_chars(line).strip().split('/')
				if len(parts)>1: flags = [char for char in parts[1]]
				else: flags = []
				self.root_flags[parts[0]] = flags
				self.root_list.append((parts[0],flags))
				no_sp = self._remove_spec_chars(parts[0])
				if no_sp not in self.root_flags:
					self.root_flags[no_sp] = flags
					self.root_list.append((no_sp,flags))
				if 'G' in flags:
					self._construct_forms(parts[0],flags)
			self.root_list = sorted(self.root_list, key=lambda x:x[0])

	def _read_in_rules(self, rule_file):
		with xlrd.open_workbook(rule_file) as wb:
			sheet = wb.sheet_by_name('affixes')
			if sheet.nrows==0: return
			heads = [x for x in sheet.row_values(0) if x]
			for r in range(1,sheet.nrows):
				row = sheet.row_values(r)
				if row[0] not in self.morph_rules: self.morph_rules[row[0]] = []
				rule = {heads[i]:row[i] for i in range(1,len(row))}
				rule['pos'] = '|'.join([x[0] for x in re.findall('[a-z]+', rule['pos'])])
				rule['stem_ending'] = self._convert_spec_chars(rule['stem_ending'])
				rule['morph_ending'] = self._convert_spec_chars(rule['morph_ending'])
				self.morph_rules[row[0]].append(rule)

	def _read_in_pronouns(self, rule_file):
		with xlrd.open_workbook(rule_file) as wb:
			sheet = wb.sheet_by_name('pronouns')
			if sheet.nrows==0: return
			heads = [x for x in sheet.row_values(0) if x]
			for r in range(1,sheet.nrows):
				row = sheet.row_values(r)
				row[0] = self._convert_spec_chars(row[0])
				rule = {heads[i]:row[i] for i in range(1,len(row))}
				rule['pos'] = '|'.join([x[0] for x in re.findall('[a-z]+', rule['pos'])])
				rule['stem_ending'] = self._convert_spec_chars(rule['stem_ending'])
				rule['morph_ending'] = self._convert_spec_chars(rule['morph_ending'])
				if row[0] not in self.word_feats:
					self.word_feats[row[0]] = [rule]
					self.word_lemmas[row[0]] = [row[0]]
				else:
					self.word_feats[row[0]].insert(0, rule)
					self.word_lemmas[row[0]].insert(0, row[0])
				no_sp = self._remove_spec_chars(row[0])
				if no_sp not in self.word_feats:
					self.word_feats[no_sp] = [rule]
					self.word_lemmas[no_sp] = [no_sp]
				else:
					self.word_feats[no_sp].append(rule)
					self.word_lemmas[no_sp].append(no_sp)

	def _read_in_contractions(self, rule_file):
		with xlrd.open_workbook(rule_file) as wb:
			sheet = wb.sheet_by_name('contractions')
			if sheet.nrows==0: return
			for r in range(1,sheet.nrows):
				row = [self._convert_spec_chars(x) for x in sheet.row_values(r) if x]
				self.contractions[row[0]] = row[1]

	def _read_in_entities(self, rule_file):
		with xlrd.open_workbook(rule_file) as wb:
			sheet = wb.sheet_by_name('entities')
			for r in range(sheet.nrows):
				row = sheet.row_values(r)
				depth = self._get_depth(row)
				subtree = self.entity_tree
				for d in range(depth):
					subtree = subtree[1][-1]
				subtree[1].append([row[depth],[]])

	def _get_depth(self, row):
		depth = 0
		for cell in row:
			if cell: return depth
			else: depth += 1
		return 0 # No cells with contents

	def _convert_spec_chars(self, text):
		text = text.replace(u'\'a', u'\xe1').replace(u'\'e', u'\xe9').replace(u'\'i', u'\xed')
		text = text.replace(u'\'o', u'\xf3').replace(u'\'u', u'\xfa').replace(u'\"u', u'\xfc')
		text = text.replace(u'\'A', u'\xc1').replace(u'\'E', u'\xc9').replace(u'\'I', u'\xcd')
		text = text.replace(u'\'O', u'\xd3').replace(u'\'U', u'\xda').replace(u'\"U', u'\xdc')
		text = text.replace(u'\'n', u'\xf1').replace(u'\'N', u'\xd1')
		return text

	def _remove_spec_chars(self, text):
		text = text.replace(u'\xe1', u'a').replace(u'\xe9', u'e').replace(u'\xed', u'i')
		text = text.replace(u'\xf3', u'o').replace(u'\xfa', u'u').replace(u'\xfc', u'u')
		text = text.replace(u'\xc1', u'A').replace(u'\xc9', u'E').replace(u'\xcd', u'I')
		text = text.replace(u'\xd3', u'O').replace(u'\xda', u'U').replace(u'\xdc', u'U')
		text = text.replace(u'\xf1', u'n').replace(u'\xd1', u'N')
		return text

	def split_contractions(self, text):
		words = text.split()
		for w in range(len(words)):
			for (key, value) in self.contractions.items():
				match = re.match(key+'$', words[w].lower())
				if match:
					if re.match('[(|]', key):
						nums = [int(x) for x in re.findall('(?<=\$)[0-9]+',value)]
						groups = [self._remove_spec_chars(match.group(x).lower()) for x in nums]
						stem = groups[nums.index(1)]
						if stem not in self.root_flags and stem not in self.word_feats:
							root = self.lemmatize(stem)
						if stem in self.root_flags or stem in self.word_feats:
							words[w] = ' '.join(groups)
					else:
						if re.match('[A-Z]+$', words[w]):
							words[w] = value.upper()
						elif re.match('[A-Z]', words[w]):
							words[w] = ' '.join([tok[0].upper() + tok[1:] \
												 for tok in value.split()])
						else: words[w] = value
		return ' '.join(words)

	def extract_word_features(self, word, pos=None):
		if re.match('n',pos) and re.search('[_.]|^[A-Z]+$|^[0-9]+$', word):
			return {'pos':'n','gender':'','number':''}
		orig_word = word
		word = word.lower()
		feat_groups = []
		for attempt in range(2):
			if word in self.word_feats:
				if pos:
					for feats in self.word_feats[word]:
						if re.match(feats['pos'], pos.lower()):
							feat_groups.append(feats)
				else: feat_groups = self.word_feats[word]
			if feat_groups: break
			if attempt == 0 and word in self.root_flags:
				self._construct_forms(word, self.root_flags[word])
			elif attempt == 0:
				root = self.lemmatize(word) # also constructs and stores root's forms
		if len(feat_groups) == 1: return feat_groups[0]
		if pos and re.match('v', pos):
			defaults = {'mood':'indicative','person':'third','tense':'present'}
		elif re.match('[A-Z]', orig_word[0]):
			defaults = {'number':'','gender':''}
		else:
			defaults = {'number':'plural' if word[-1]=='s' else 'singular'}
			if re.search('d(es?)$|as?$|i[oó]n(es)?$', word): defaults['gender'] = 'female'
			elif re.search('l$|[stlu]es?$', word): defaults['gender'] = ''
			else: defaults['gender'] = 'male'
		if len(feat_groups) > 1:
			pos = self._most_common_value(feat_groups, 'pos')
			subgroups = [feats for feats in feat_groups if feats['pos'] == pos]
			if len(subgroups) == 1: return subgroups[0]
			for feat,value in defaults.items():
				subgroups2 = [feat_group for feat_group in subgroups \
							  if feat in feat_group and feat_group[feat] == value]
				if len(subgroups2) == 1: return subgroups2[0]
				elif len(subgroups2) > 1: subgroups = subgroups2
			if subgroups: return subgroups[0]
		if feat_groups: return feat_groups[0]
		else: return defaults
		return {}

	def _most_common_value(self, feat_groups, feat):
		val_counts = {}
		for feat_group in feat_groups:
			if feat_group[feat] not in val_counts:
				val_counts[feat_group[feat]] = 1
			else: val_counts[feat_group[feat]] += 1
		if not val_counts: return ''
		return sorted(val_counts.items(), key=lambda x:x[1], reverse=True)[0][0]

	def lemmatize(self, word, pos=None):
		word = word.lower()
		for attempt in range(2):
			if word in self.word_lemmas:
				if pos:
					for lemma in self.word_lemmas[word]:
						if re.match(self.word_feats[lemma][0]['pos'], pos.lower()):
							return lemma
				else: return self.word_lemmas[word][0]
			elif attempt == 0:
				i = bisect_left(self.root_list, (word,))
				j = i - 1
				cont_left = i > 0
				cont_right = j < len(self.root_list) - 1
				while cont_left or cont_right:				
					if cont_left and i > 0 and self.root_list[i-1][0][0] == word[0]:
						i -= 1
						self._construct_forms(self.root_list[i][0], self.root_list[i][1])
						if word in self.word_lemmas: break
					else: cont_left = False
					if cont_right and j < len(self.root_list)-1 and self.root_list[j+1][0][0] == word[0]:
						j += 1
						self._construct_forms(self.root_list[j][0], self.root_list[j][1])
						if word in self.word_lemmas: break
					else: cont_right = False
				self.root_list = self.root_list[:i] + self.root_list[j+1:]
		return word

	def nominalize(self, word):
		word = word.lower()
		if word in self.nom_forms: return self.nom_forms[word]
		if word in self.root_flags and \
		('H' in self.root_flags[word] or 'I' in self.root_flags[word]):
			self._construct_forms(word, self.root_flags[word])
			if word in self.nom_forms: return self.nom_forms[word]
		root = lemmatize(word)
		if root in self.nom_forms: return self.nom_forms[root]
		return word

	def _construct_forms(self, root, flags):
		for flag in flags:
			if flag in self.morph_rules:
				for rule in self.morph_rules[flag]:
					match = re.match('(.*)('+rule['stem_ending']+')$', root)
					if match:
						form = match.group(1)+rule['morph_ending']
						if form not in self.word_feats:
							self.word_feats[form] = [rule]
							self.word_lemmas[form] = [root]
						else:
							self.word_feats[form].insert(0, rule)
							self.word_lemmas[form].insert(0, root)
						no_sp = self._remove_spec_chars(form)
						if no_sp not in self.word_feats:
							self.word_feats[no_sp] = [rule]
							self.word_lemmas[no_sp] = [root]
						else:
							self.word_feats[no_sp].append(rule)
							self.word_lemmas[no_sp].append(root)
						if re.match('H|I', flag):
							if root not in self.nom_forms:
								self.nom_forms[root] = [form]
							else: self.nom_forms[root].insert(0, form)
							no_sp = self._remove_spec_chars(root)
							if no_sp not in self.nom_forms:
								self.nom_forms[no_sp] = [form]
							else: self.nom_forms[no_sp].append(form)

	def get_entity_path(self, node):
		(match1, path1) = self._get_entity_tree_path(self.entity_tree, node['form'])
		if match1 and path1:
			return path1[1:]
		phrasetoks = [tok for (tok,lem,tag,dep) in node['premods']]+[node['form']]+ \
					 [tok for (tok,lem,tag,dep) in node['postmods']]
		phrase = ' '.join(phrasetoks)
		(match2, path2) = self._get_entity_tree_path(self.entity_tree, phrase)
		if match2 and path2:
			return path2[1:]
		return []

	def _get_entity_tree_path(self, entity_tree, phrase):
		match = False
		path = []
		if re.search(':', entity_tree[0]):
			parts = entity_tree[0].split(':')
			if re.search('\\b('+parts[1]+')', phrase.lower()):
				path.append(parts[0])
				match = True
		else: path.append(entity_tree[0])
		if len(entity_tree)>1 and type(entity_tree[1])==list:
			for subtree in entity_tree[1]:
				match, subpath = self._get_entity_tree_path(subtree, phrase)
				if match:
					path.extend(subpath)
					break
		return match, path



