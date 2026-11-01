from bs4 import BeautifulSoup
import requests
import html5lib
import random
import os
from urllib.parse import quote

DEXONLINE_BASE_URL = os.environ.get('DEXONLINE_BASE_URL', 'https://dexonline.ro').rstrip('/')
DEXONLINE_TIMEOUT = float(os.environ.get('DEXONLINE_TIMEOUT', '15'))
DEXONLINE_DEFINITION_SELECTOR = os.environ.get('DEXONLINE_DEFINITION_SELECTOR', 'span.def')


"""
	Function getWordOfThe
	Required @link
	Return @list

	Universal function that receives a link and returns a list of definition (word and definition)
"""
def getWordOfThe(link=None):
	# Call function to get spans by link
	spans = getTags(link, 'span', 'def')

	definition = []
	for span in spans:
		try:
			word = span.find('b').text
			definition.append(str(word).strip())

			span.find("b").extract()
			definition.append(span.text.strip())

		except:
			error = 'Error that will not be displayed :D'
	return definition

"""
	Function getWordOfThe
	Required @link
	Return @list

	Universal function that receives a link and returns the span tags
"""
def getTags(link=None, tag=None, clas=None):
	response = requests.get(link, timeout=DEXONLINE_TIMEOUT, headers={'User-Agent': 'mini-cuvinte-dexonline-api/0.1'})
	response.raise_for_status()
	soup = BeautifulSoup(response.content, features="html5lib")
	spans = soup.select(DEXONLINE_DEFINITION_SELECTOR) if tag == 'span' and clas == 'def' else soup.find_all(str(tag), str(clas))

	return spans

"""
	Function toString
	Required @list or @listOfLists
	Return nothing
	Print word and definition
	Ex:
		WORD: Default word
		DEFINITION: Default definition

	Work for function: getWordDefinition, getWordOfTheDay, getWordOfTheMonth
"""
def toString(listOfDefinition=['Default word', 'Default definition']):
	if str(type(listOfDefinition[0])) == "<class 'list'>":
		for definition in listOfDefinition:
			print('WORD: ' + str(definition[0]))
			print('DEFINITION: ' + str(definition[1]) + '\n')

	elif str(type(listOfDefinition[0])) == "<class 'str'>" and len(listOfDefinition) <= 2:
		print('WORD: ' + str(listOfDefinition[0]))
		print('DEFINITION: ' + str(listOfDefinition[1]) + '\n')

	elif str(type(listOfDefinition[0])) == "<class 'str'>" and len(listOfDefinition) >= 2:
		print('PARADIGMS: ' + str(listOfDefinition))

"""
	Function getWordDefinition
	Required @word
	Return @listOfLists

	In every list is present: word and definition
"""
def getWordDefinition(word=None):
	link = DEXONLINE_BASE_URL + '/definitie/' + quote(str(word), safe='') + '/expandat'

	# Call function to get spans by link
	spans = getTags(link, 'span', 'def')

	definition = []
	for span in spans:
		wordDef = []
		try:
			word = span.find("b").text
			wordDef.append(str(word).strip())
			span.find("b").extract()

			for word in span:
				wordDef.append(span.text.strip())

			if wordDef[1] != '' or wordDef[1] != '':
				definition.append(wordDef)
		except:
			error = 'Error that will not be displayed :D'
	return definition

"""
	Function getWordOfTheDay
	Required nothing
	Return @list
	
	In list is present: word and definition
"""
def getWordOfTheDay():
	link = DEXONLINE_BASE_URL + '/cuvantul-zilei'
	return getWordOfThe(link)

"""
	Function getWordOfTheMonth
	Required nothing
	Return @list
	
	In list is present: word and definition
"""
def getWordOfTheMonth():
	link = DEXONLINE_BASE_URL + '/cuvantul-lunii'
	return getWordOfThe(link)

"""
	Function getParadigms
	Required @word
	Return @list
	
	In list is present: words
"""
def getParadigms(word=None):
	link = DEXONLINE_BASE_URL + '/definitie/' + quote(str(word), safe='') + '/expandat/paradigma'

	uls = getTags(link, 'ul', 'commaList')

	paradigms = []
	for ul in uls:
		paradigms.append(ul.find("li").text.strip())

	paradigms = list(set(paradigms))

	return paradigms
"""
	Function reallyExist
	Required @word
	Return @Boolean

	loc_flexiuni_6_0 is a list of romanian words - by dexonline.ro
"""
def reallyExist(word=None):
	wordsFile = open("loc-flexiuni-6.0.txt", "r", encoding="utf-8")

	loc_flexiuni_6_0 = []
	for line in wordsFile:
	  stripped_line = line.strip()
	  loc_flexiuni_6_0.append(stripped_line)

	wordsFile.close()
	return True if str(word) in loc_flexiuni_6_0 else False

"""
	Function randomWord
	Required nothing
	Return @randomWord
"""
def randomWord():
	link = DEXONLINE_BASE_URL + "/cuvinte-aleatorii"

	divs = getTags(link, 'div', 'col-md-12 main-content')

	words = []
	for div in divs:
		div.find("section").extract()
		hrefs = div.find_all('a')
	
	for href in hrefs:
		words.append(href.text)

	randomWord = random.choice(words)
	return randomWord