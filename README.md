# Pepperplate-Importer

A python script to import recipes from various websites to a [Pepperplate](http://www.pepperplate.com/) account.

## Supported Recipe Websites
* [Blue Apron](https://www.blueapron.com/cookbook)

## Dependencies

Python 3.

```bash
pip3 install -r requirements.txt
```

## Usage
Input your Pepperplate login credentials and list of recipes with tags (optional) in `config.py`:

```python
pp_username = "user@example.com"
pp_password = "password"
recipes = {
	"https://www.blueapron.com/recipes/chicken-fresh-basil-fettuccine-with-tomato-cream-sauce" : ["dinner", "pasta", "chicken"]
}
```

Run the script:

```bash
python3 pepperplate_importer.py
```

Cheers!