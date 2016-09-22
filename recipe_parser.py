import requests
from collections import namedtuple
from bs4 import BeautifulSoup

Recipe = namedtuple('Recipe', 'title subtitle imgURL description cook_time recipe_yield ingredients instructions source url tags')

def parseBlueApron(session, url, tags):
	try:
		r = session.get(url)
		parsed_html = BeautifulSoup(r.content, 'html.parser')

		title = parsed_html.body.find('h1', attrs={'class':'main-title'}).text.replace('\n', '')
		subtitle = parsed_html.body.find('h2', attrs={'class':'sub-title'}).text.replace('\n', '')
		imgURL = parsed_html.body.find('img', attrs={'class':'rec-splash-img'})['src']
		description = parsed_html.body.find('p', attrs={'itemprop':'description'}).text
		cook_time = parsed_html.body.find('div', attrs={'class':'nutrition-information row'}).find('div', attrs={'class':'col-xs-4'}).text.replace('\n','')[len('Cook Time'):] # Remove beginning 'Cook Time'
		recipe_yield = parsed_html.body.find('span', attrs={'itemprop':'recipeYield'}).text
		ingredients = [li.text.replace('\n','') for li in parsed_html.body.find('ul', attrs={'class':'ingredients-list'}).findAll('li')]
		instructions = [li.text.replace('\n','') for li in parsed_html.body.find('section', attrs={'class':'section-rec-instructions container'}).findAll('div', attrs={'class':'instr-txt'})]

		return Recipe(title, subtitle, imgURL, description, cook_time, recipe_yield, ingredients, instructions, "Blue Apron", url, tags)

	except requests.exceptions.RequestException:
		return None

SUPPORTED_WEBSITES = {
	"blueapron.com" : parseBlueApron
}