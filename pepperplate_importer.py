import requests
import re
import config
import recipe_parser
from bs4 import BeautifulSoup
from progress.bar import Bar

PP_LOGIN_URL = "https://www.pepperplate.com/login.aspx"
PP_LOGIN_PARAMS = {
	"__EVENTTARGET":"ctl00$cphMain$loginForm$ibSubmit",
	"__VIEWSTATE":"/wEPDwUKLTcxOTM1MDY3Mw9kFgJmD2QWAgIBD2QWBmYPFgIeB1Zpc2libGVoZAIBDxYCHwBnZAIFD2QWAgIBD2QWAgIBD2QWAmYPZBYCAgEPFgIfAGhkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSRjdGwwMCRjcGhNYWluJGxvZ2luRm9ybSRjYlJlbWVtYmVyTWX6+EFLFMRKbfydmpUj4wAPc7mvB44zvf0PSqv5gYc/oQ==",
	"__VIEWSTATEGENERATOR":"C2EE9ABB",
	"__EVENTVALIDATION":"/wEdAAa/1rXdVU0+E4I6qe/8/1vr5NjnQnV3ACakt+OFoq/poIk+G0F2hkBAuVGSTeHfUEPAXUaOb/COCTyxdHOCu+1TWS9Byv/QKTlj8oYJ3PuJaAwq+cY+TuM+f6PEOa5kpFdLxoWu1SzyQ+dSe4wMXUj8COE0cW4aUjyR8doM83m83w==",
	"ctl00$cphMain$loginForm$tbEmail":config.pp_username,
	"ctl00$cphMain$loginForm$tbPassword":config.pp_password
}

PP_CREATE_RECIPE_URL = "http://www.pepperplate.com/recipes/createm.aspx"
PP_CREATE_RECIPE_PARAMS = [
	("__VIEWSTATE", "/wEPDwULLTE5NzkyODYxNzYPFgIeE1ZhbGlkYXRlUmVxdWVzdE1vZGUCARYCZg8PFgIeEFNlbGVjdGVkTmF2SW5kZXhmZBYCAgEPZBYIAgEPDxYCHgRUZXh0BQR0ZXN0ZGQCAg8PFgIeC05hdmlnYXRlVXJsBShodHRwczovL3d3dy5wZXBwZXJwbGF0ZS5jb20vcHJvZmlsZS5hc3B4ZGQCBA8WAh4FY2xhc3MFBmFjdGl2ZWQCCA9kFgICAQ8WAh8CBQEwZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUWY3RsMDAkY3BoTWlkZGxlJGliU2F2ZbxuCL1ICEQLp0S2q1Sa9xKuExojj/ehKw7WrA+1k3WL"),
	("__VIEWSTATEGENERATOR", "CEDB596F"),
	("__EVENTVALIDATION", "/wEdAA0cSXgwIwYdJDhN8JoWZorWKaO6Dhd1lpo6in2sbzMy5Sr3+qKtIL3NW9+RTnE+UYIHcCYTrnvn/vctuXuPhQgNoVrVSFfrsJIZ9h8jsXnYwrmEG9JMPQJsPduPSFwoDJclNMSwBsqoUBelGVO5A+L5BlMVm+eNqEvh3FfkXMBOdqSkzk5l6BlV9HbM9dIGxL42rQgLWHNIFdwS9eNLDFGO7rVrROtrdPv+wHCGES6QWwQV3Zm+c3GHTampJlrGRFzOBBzqedUx1XrrF+IhjDuIv1aAS7I47rJQKgZMlIuTGi2aijy6VRpeKkZ8ZzavF7g="),
	("ctl00$cphMiddle$ibSave.x", "0"),
	("ctl00$cphMiddle$ibSave.y", "0")
]

PP_UPLOAD_IMG_URL = "http://www.pepperplate.com/upload/recipeimage.ashx"
PP_UPLOAD_IMG_PARAMS = {
	"Filename":(None, "image.jpg"),
	"fileext":(None, "*.jpg;*.jpeg;*.png"),
	"folder":(None, "/recipes/"),
	"Upload":(None, "Submit Query")
}

PP_AUTH_COOKIE = ".ASPXAUTH"
PP_RECIPE_URL_ID_PATTERN = "^http:\/\/www.pepperplate\.com\/recipes\/view\.aspx\?id=(.*)$"
URL_DOMAIN_PATTERN = "^https?:\/\/(?:www\.)?(.*?)\/.*$"

def pepperplateLogin(session):
	try:
		r = session.post(PP_LOGIN_URL, data=PP_LOGIN_PARAMS)
		return r.url != PP_LOGIN_URL # Success if we weren't redirected back to the login URL
	except requests.exceptions.RequestException:
		return False

def pepperplateCreateRecipe(session, recipe):
	try:
		params = PP_CREATE_RECIPE_PARAMS[:]
		params.extend([
			("ctl00$cphMiddle$tbTitle", "%s %s" % (recipe.title, recipe.subtitle)),
			("ctl00$cphMiddle$tbDescription", recipe.description),
			("ctl00$cphMiddle$tbIngredients", '\n'.join(recipe.ingredients)),
			("ctl00$cphMiddle$tbDirections", '\n'.join(recipe.instructions)),
			("ctl00$cphMiddle$tbYield", recipe.recipe_yield),
			("ctl00$cphMiddle$tbActiveTime", ""),
			("ctl00$cphMiddle$tbTotalTime", recipe.cook_time),
			("ctl00$cphMiddle$tbSource", recipe.source),
			("ctl00$cphMiddle$tbUrl", recipe.url),
			("ctl00$cphMiddle$tbNotes", "")
		])

		# Add all the tags
		for tag in recipe.tags:
			params.append(("tagSelection[]", tag))

		r = session.post(PP_CREATE_RECIPE_URL, data=params)

		if r.url == PP_LOGIN_URL: # Failure if we were redirected back to the login URL
			return False

		# Get the recipe ID
		recipeId = re.search(PP_RECIPE_URL_ID_PATTERN, r.url).group(1)

		# Upload the image
		return pepperplateUploadImage(session, recipeId, recipe.imgURL)
	except requests.exceptions.RequestException:
		return False

def pepperplateUploadImage(session, recipeId, imgURL):
	try:
		# Get the image data
		r = session.get(imgURL)

		# Post the image to the recipe
		params = dict(PP_UPLOAD_IMG_PARAMS)
		params.update({
			"auth":(None, session.cookies[PP_AUTH_COOKIE]),
			"recipeId":(None, recipeId),
			"Filedata":("image.jpg", r.content, "application/octet-stream")
			})
		r2 = session.post(PP_UPLOAD_IMG_URL, files=params)

		return r2.status_code == 200
	except requests.exceptions.RequestException:
		return False

def main():
	session = requests.Session()
	if pepperplateLogin(session):
		# Set up progress bar
		bar = Bar("Importing Recipes", max=len(config.recipes))

		num_succeeded = 0
		for url, tags in config.recipes.items():
			bar.next()
			domain = re.search(URL_DOMAIN_PATTERN, url).group(1)
			if domain in recipe_parser.SUPPORTED_WEBSITES.keys():
				recipe = recipe_parser.SUPPORTED_WEBSITES[domain](session, url, tags)
				if recipe is not None:
					if pepperplateCreateRecipe(session, recipe):
						num_succeeded += 1

		bar.finish()

		print("\033[92m%s Imported\033[0m | \033[91m%s Failed\033[0m" % (num_succeeded, len(config.recipes) - num_succeeded))
	else:
		print("\033[91mFailed to log in to Pepperplate.\033[0m")

if __name__ == "__main__":
    main()