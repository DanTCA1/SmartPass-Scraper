## SmartPass Scraper

Scrapes names and emails off of SmartPass's servers for a specific school, sorts them into categories based on email, and than outputs them into a file.

# Usage
> [!WARNING]
>
> Use this at your own discretion. It is not my fault if you get in trouble while using this.

1. Download `Scraper.py`.
1. Run it once, letting it generate `Config.json`.
1. Fill in all of the temporary values with your own.
    * If you have no need to sort by email, leave all identifiers as `""`.
    * Inversely, infinite sort options can be added in the `Misc Identifiers` section.
    * Your token can be found using inspect element (`ctrl + shift + i`), going to your network tab, and reloading.
> [!IMPORTANT]
> 
> Make sure that you only grab the `smartpassToken` cookie, and leave the other two.

4. Run the script again (this may take a while depending on how many students there are).
1. Use `Output.json` however you wish.
