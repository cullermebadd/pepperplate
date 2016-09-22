import requests
from collections import namedtuple
from bs4 import BeautifulSoup

Recipe = namedtuple('Recipe', 'title imgURL description active_time total_time recipe_yield ingredients instructions notes source url tags')

def parseBlueApron(session, url, tags):
	try:
		r = session.get(url)
		parsed_html = BeautifulSoup(r.content, 'html.parser')

		title = parsed_html.body.find('h1', attrs={'class':'main-title'}).text.replace('\n', '')
		subtitle = parsed_html.body.find('h2', attrs={'class':'sub-title'}).text.replace('\n', '')
		imgURL = parsed_html.body.find('img', attrs={'class':'rec-splash-img'})['src']
		description = parsed_html.body.find('p', attrs={'itemprop':'description'}).text
		total_time = parsed_html.body.find('div', attrs={'class':'nutrition-information row'}).find('div', attrs={'class':'col-xs-4'}).text.replace('\n','')[len('Cook Time'):] # Remove beginning 'Cook Time'
		recipe_yield = parsed_html.body.find('span', attrs={'itemprop':'recipeYield'}).text
		ingredients = [li.text.replace('\n','') for li in parsed_html.body.find('ul', attrs={'class':'ingredients-list'}).findAll('li')]
		instructions = [li.text.replace('\n','') for li in parsed_html.body.find('section', attrs={'class':'section-rec-instructions container'}).findAll('div', attrs={'class':'instr-txt'})]

		return Recipe("%s %s" % (title, subtitle), imgURL, description, None, total_time, recipe_yield, ingredients, instructions, None, "Blue Apron", url, tags)

	except requests.exceptions.RequestException:
		return None

def parseSeriousEats(session, url, tags):
	try:
		r = session.get(url)
		parsed_html = BeautifulSoup(r.content, 'html.parser')

		title = parsed_html.body.find('h1', attrs={'class':'recipe-title fn'}).text.replace(" Recipe", "") # Strip 'Recipe', common on end of SE recipes
		imgURL = parsed_html.body.find('img', attrs={'class':'photo'})['src']
		description = parsed_html.body.find('div', attrs={'class':'recipe-introduction-body'}).findAll('p')[1].text
		active_time = parsed_html.body.find('ul', attrs={'class':'recipe-about'}).findAll('span')[3].text
		total_time = parsed_html.body.find('ul', attrs={'class':'recipe-about'}).findAll('span')[5].text
		recipe_yield = parsed_html.body.find('ul', attrs={'class':'recipe-about'}).findAll('span')[1].text

		ingredients_html = parsed_html.body.findAll('li', attrs={'class':'ingredient'})
		ingredients = []
		for ingredient in ingredients_html:
			# Check if the ingredient is a header (it contains a strong tag)
			if ingredient.find('strong'):
				ingredients.append("[%s]" % ingredient.text)
			else:
				ingredients.append(ingredient.text)

		instructions_html = parsed_html.body.findAll('div', attrs={'class':'recipe-procedure-text'})
		instructions = []
		for instruction in instructions_html:
			instructions.append(instruction.find('p').text)

		# Check if we have any notes
		possible_notes_group_html = parsed_html.body.findAll('h6', attrs={'class':'callout-title'})
		notes = None
		for possible_notes_html in possible_notes_group_html:
			if possible_notes_html.text == "Notes:":
				notes = possible_notes_html.next_sibling.next_sibling.text

		return Recipe(title, imgURL, description, active_time, total_time, recipe_yield, ingredients, instructions, notes, "Serious Eats", url, tags)

	except requests.exceptions.RequestException:
		return None

SUPPORTED_WEBSITES = {
	"blueapron.com" : parseBlueApron,
	"seriouseats.com" : parseSeriousEats
}