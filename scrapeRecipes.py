#!/usr/bin/env python3

#
# Scrape recipes from pepperplate.com.
#

import requests
from bs4 import BeautifulSoup
import lxml.html
import json
import time
import getpass
import re
import os
import json
from collections import namedtuple
#import config

def printToFile(content):
    f = open('out.txt', 'w')
    #print >> f, 'Filename:', "test"  # or f.write('...\n')
    f.write(content)
    f.close()

class pepperplate_recipe:
    def __init__(self, id, html):
        self.id = id
        self.soup = BeautifulSoup(html)

    def get_id(self):
        return self.id

    def get_title(self):
        element = self.soup.find(id='cphMiddle_cphMain_lblTitle')
        if element:
            return element.get_text().strip()
        return None

    def get_description(self):
        element = self.soup.find(id='cphMiddle_cphMain_lblDescription')
        if element:
            return element.get_text().strip()
        return None

    def get_imgURL(self):
        return self.soup.find(id='cphMiddle_cphMain_imgRecipeThumb')['src']

    def get_active_time(self):
        element =  self.soup.find(id='cphMiddle_cphMain_lblActiveTime')
        if element:
            return element.get_text().strip()
        return None

    def get_total_time(self):
        element = self.soup.find(id='cphMiddle_cphMain_lblTotalTime')
        if element:
            return element.get_text().strip()
        return None

    def get_recipe_yield(self):
        element =  self.soup.find(id='cphMiddle_cphMain_lblYield')
        if element:
            return element.get_text().strip()
        return None

    def get_notes(self):
        element =  self.soup.find(id='cphMiddle_cphMain_lblNotes')
        if element:
            return element.get_text().strip()
        return None

    def get_source(self, source):
        if source:
            return source.get_text().strip()
        return None

    def get_url(self, source):
        if source:
            print("\n URL: %s" % source)
            return source['href']

    def get_ingredient_groups(self, ul):
        if ul:
            ingredient_groups = []

            groups = ul.findAll('li', recursive=False)

            for group in groups:
                ingredient_group = {}
                heading = ""

                # group heading
                h4 = group.find('h4')
                if h4:
                    heading = h4.text.strip()

                items = group.findAll('li', attrs={'class':'item'})

                ingredient_items = []

                #ingredients in a group
                for item in items:
                    ingredient_item = {}

                    # ingredient quantity
                    quantity_el = item.find('span', attrs={'class':'ingquantity'})
                    if quantity_el:
                        quantity = quantity_el.text.strip()

                        ingredient_item['quantity'] = quantity

                    # ingredient
                    ingredient_el = item.find('span', attrs={'class':'content'})
                    if ingredient_el:
                        ingredient = ""
                        for string in ingredient_el.stripped_strings:
                            ingredient = string

                        ingredient_item['item'] = ingredient

                    # add ingredient item to items
                    ingredient_items.append(ingredient_item)

                ingredient_group = {
                    "heading" : heading
                    ,"items": ingredient_items
                }

                ingredient_groups.append(ingredient_group)

        return ingredient_groups

    def get_direction_groups(self, ul):
        if ul:
            direction_groups = []

            groups = ul.findAll('li', recursive=False)

            for group in groups:
                direction_group = {}
                heading = ""

                # group heading
                h4 = group.find('h4')
                if h4:
                    heading = h4.text.strip()

                items = group.findAll('li')

                direction_items = []

                #direction in a group
                for item in items:
                    direction_item = {}

                    # direction
                    direction = item.find('span', attrs={'class':'text'})
                    if direction:
                        direction = direction.text.strip()

                    # add direction item to items
                    direction_items.append(direction)

                direction_group = {
                    "heading" : heading
                    ,"items": direction_items
                }

                direction_groups.append(direction_group)

        return direction_groups

    def get_new_body(self):
        new_soup = BeautifulSoup('<html><head></head><body></body></html>')

        thumb = self.get_thumbnail()
        if thumb:
            hdr = new_soup.new_tag('img')

            hdr['src'] = './img/{}'.format(self.id + '.jpg')
            new_soup.body.append(hdr)

        #source
        source = self.soup.find(id='cphMiddle_cphMain_hlSource')

        #ingredients
        item = self.soup.find('ul', {'class':'inggroups'})
        if item:
            groups = self.get_ingredient_groups(item)

        #instructions
        item = self.soup.find('ul', {'class':'dirgroups'})
        if item:
            dirGroups = self.get_direction_groups(item)

        recipe = {
            "title" : self.get_title(),
            "description" : self.get_description(),
            "imgURL" : self.get_imgURL(),
            "active_time" : self.get_active_time(),
            "total_time" : self.get_total_time(),
            "recipe_yield" : self.get_recipe_yield(),
            "notes" : self.get_notes(),
            "source" : self.get_source(source),
            "url" : self.get_url(source),
            "ingredient_groups" : groups,
            "direction_groups" : dirGroups
        }

        #return new_soup.prettify('latin-1')
        return recipe

    def get_thumbnail(self):
        tmp = self.soup.find(id='cphMiddle_cphMain_imgRecipeThumb')
        if tmp:
            return tmp['src']
        else:
            return None

class pepperplate:

    def __init__(self, hostname):
        self.hostname = hostname
        self.last_page = False
        self.session = requests.Session()

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password

    def login(self):
        if self.username == None or self.password == None:
            print('No login details supplied')
            return False

        url = 'https://{}/login.aspx'.format(self.hostname)

        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36"}

        self.session.headers.update(headers)
        r = self.session.get(url)

        login_page = lxml.html.fromstring(r.content)
        VIEWSTATE = login_page.xpath('//input[@id="__VIEWSTATE"]/@value')[0]
        EVENTVALIDATION = login_page.xpath('//input[@id="__EVENTVALIDATION"]/@value')[0]

        login_data={"__VIEWSTATE":VIEWSTATE,
        "__EVENTVALIDATION":EVENTVALIDATION,
        "__EVENTARGUMENT":'',
        "__EVENTTARGET":'ctl00$cphMain$loginForm$ibSubmit',
        "ctl00$cphMain$loginForm$tbEmail":self.username,
        "ctl00$cphMain$loginForm$tbPassword":self.password,
        "ctl00$cphMain$loginForm$cbRememberMe":'on'
        }

        r = self.session.post(url, data=login_data)
        if r.url != 'http://{}/recipes/default.aspx'.format(self.hostname):
            print('Login failure')
            return False

        return True


    def get_page(self, page):

        url = 'http://{}/recipes/default.aspx/GetPageOfResults'.format(self.hostname)
        parameters = json.dumps({'pageIndex':page,
                                 'pageSize':20,
                                 'sort':4,
                                 'tagIds': [],
                                 'favoritesOnly':0})

        headers={'Referer':'http://{}/recipes/default.aspx'.format(self.hostname)
                         ,'Content-Type': 'application/json'
                         #,'X-Requested-With': 'XMLHttpRequest'
                         #,'DNT':1
                         #,'Accept': 'application/json, text/javascript, */*; q=0.01'
                         #,'Accept-Language': 'en,de;q=0.7,en-US;q=0.3'
                         #,'Accept-Encoding': 'gzip, deflate'
                         }

        print("\n%s" % url)
        r = self.session.request('POST', url, data=parameters, headers=headers)

        print("\nresponse: %s" % r)

        page = lxml.html.fromstring(r.json()['d'])
        self.page = [re.findall(r'id=(\d+)', a)[0] for a in page.xpath('//div[@class="item"]/p/a/@href')]
        self.last_page = len(self.page) < 20

        return self.page

    def get_recipe(self, id):
        url = 'http://{}/recipes/view.aspx?id={}'.format(self.hostname, id)
        r = self.session.request('GET', url)
        return r.content

    def get_url(self, url):
        r = requests.get(url)
        return r.content

    def is_last_page(self):
        return self.last_page

    def is_logged_in(self):
        return self.session != None

# def save_recipe(recipe, savepath):
#     filename = recipe.get_title().replace('/','_').replace('"', '').replace(':','').replace(' ','_')
#     with open(savepath + '/{}.{}.html'.format(filename, recipe.get_id()), 'wb') as f:
#         f.write(recipe.get_new_body())
#
def save_file(img, savepath):
    with open(savepath, 'wb') as f:
        f.write(img)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrape recipies from Pepperplate')
    parser.add_argument('username', help='Username to log in with')
    parser.add_argument('password', nargs="?", default=None, help='Password to log in with. If not provided on the command line it will be requested by the program')
    parser.add_argument('directory', nargs="?", default='recipes', help='Directory to which download everything. defaults to "recipes"')
    args = parser.parse_args()

    if not args.password:
         args.password = getpass.getpass('Please enter the password for account {}: '.format(args.username))

    imgpath = os.path.join(args.directory, 'img', '{}')
    if not os.path.exists(imgpath.format("")):
        os.makedirs(imgpath, exist_ok = True)

    pp = pepperplate('www.pepperplate.com')
    pp.set_username(args.username)
    pp.set_password(args.password)
    # pp.set_username(config.pp_username)
    # pp.set_password(config.pp_password)

    if not pp.login():
        exit(1)

    page = 0

    recipes = []

    while not pp.is_last_page():
        print('Downloading page {}'.format(page+1))

        for id in pp.get_page(page):
            time.sleep(1) #sleep 1 second between requests to not mash the server
            recipe = pepperplate_recipe(id, pp.get_recipe(id))
            print('Downloaded {}'.format(recipe.get_title()))
            #save_recipe(recipe, args.directory)

            recipes.append(recipe.get_new_body())

            if recipe.get_thumbnail():
                save_file(pp.get_url(recipe.get_thumbnail()), imgpath.format(id + '.jpg'))

        page += 1

    with open('json.txt', 'w') as outfile:
        json.dump(recipes, outfile, indent=4)
