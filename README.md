# Bible.com to Zefania XML Converter

This project consists of a set of Python scripts designed to fetch Bible data from bible.com and convert it into the Zefania XML Bible format. It retrieves details such as the Bible version's name, abbreviation, publisher, language, copyright information, and the full text content including books, chapters, and verses.

## Features

* Fetches Bible metadata (name, abbreviation, language, etc.) from bible.com.
* Retrieves the list of books for a specific Bible version.
* Fetches all chapters and verses for each book.
* Uses asynchronous calls to efficiently download chapter data.
* Converts the fetched Bible data into Zefania XML format.
* Saves the output as an `.xml` file named with the Bible's abbreviation in a `Bibles` directory.

## Requirements

* Python 3.x
* `requests` library
* `lxml` library

You can install the required libraries using pip:
```bash
pip install requests lxml
