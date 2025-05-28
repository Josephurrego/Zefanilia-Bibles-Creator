import re
from lxml import html
from collections import defaultdict
import utils
from concurrent.futures import ThreadPoolExecutor, as_completed

class Bible:
    """
    Represents a specific Bible version obtained from bible.com.

    This class is initialized with a Bible version ID and automatically
    retrieves version metadata (such as name, abbreviation, publisher,
    language, and copyright description) and the list of books it contains.

    It allows accessing books individually by their USFM identifier,
    iterating over the books, and getting the total number of books.

    The books (`Bible.Book`) in turn allow fetching chapters (`Bible.Chapter`),
    with the capability to load all chapters of a book asynchronously
    for improved performance. Chapters process HTML content obtained
    from bible.com to extract verses.

    Attributes:
        id (int): The Bible version ID on bible.com.
        name (str): The localized title of the Bible.
        abrev (str): The localized abbreviation of the Bible.
        author (str): The publisher's name.
        lang (str): The ISO 639_3 language code.
        description (str): Short copyright text.
        books (list): List of `Bible.Book` objects.

    # Usage:
    ```nvi_bible = Bible(128) # New International Version
    first_book = nvi_bible.get_book("GEN") # Get Genesis
    for book in niv_bible:
        print(book.name)
    ```
    """
    def __init__(self,bible_id):
        self.id = bible_id
        data = utils.getResponse(f'https://www.bible.com/api/bible/version/{self.id}').json()
        self.name = data['local_title']
        self.abrev = data['local_abbreviation']
        self.author = data['publisher']['name']
        self.lang = data['language']['iso_639_3']
        self.description = data['copyright_short']['text']

        self.__hashMap = defaultdict(int)
        self.books = []
        idx = 0
        for i in data['books']:
            self.books.append(Bible.Book(
                i['usfm'],
                i['human_long'],
                self.id,
                len([ch for ch in i['chapters'] if ch['canonical']]),
                i['abbreviation']
                ))
            self.__hashMap[i['usfm']] = idx
            idx+=1
            
    def get_book(self,book:str):
        return self.books[self.__hashMap[book]]
    
    def __iter__(self):
        return iter(self.books)
    
    def __len__(self):
        return len(self.books)
    
    def __getitem__(self,key):
        return self.get_book(key)

    def __repr__(self):
        return f'<Bible({self.abrev})>'

    class Book:
        """
        Represents a single book within a specific Bible version.

        Each book is identified by its USFM ID and contains metadata such as
        its full name, abbreviation, and the total number of chapters it has.
        It provides methods to access individual chapters or fetch all
        chapters asynchronously.

        Attributes:
            id (str): The USFM identifier for the book (e.g., "GEN").
            name (str): The human-readable full name of the book (e.g., "Genesis").
            bible (int): The ID of the parent Bible version.
            abrev (str): The abbreviation for the book (e.g., "Gen").
            _Book__length (int): The number of chapters in this book.

        Initialization Note:
            If the 'length' (number of chapters) is not provided during
            initialization, the class will attempt to fetch this information
            via an API call. This fallback is intended for standalone use;
            when created by the `Bible` class, 'length' is pre-supplied.
        """
        def __init__(self,book_id:str,name_book:str,bible_id:int,length:int=None,abrev=None):
            self.bible = bible_id

            if length is None:
                data = utils.getResponse(f'https://www.bible.com/api/bible/version/{self.bible}').json()
                data = next(filter(lambda i:i['usfm']==self.id,data["books"]))
                length = len(data['chapters'])

            self.__length = length
            self.id = book_id
            self.abrev = abrev.replace('.','')
            self.name = name_book

        def get_chapter(self,number:int):
            return Bible.Chapter(self.id,number,self.bible)

        def get_async_chapters(self):
            chapters = {}
            with ThreadPoolExecutor(max_workers=20) as executor:
                chapterFn = lambda x:Bible.Chapter(self.id,x,self.bible)
                futureChapters = {executor.submit(chapterFn,ch): ch for ch in range(1,self.__length+1)}

                for future in as_completed(futureChapters):
                    chapters.setdefault(futureChapters[future],future.result())
            return chapters

        def __getitem__(self,key:int):
            return self.get_chapter(key)
        
        def __len__(self):
            return self.__length

        def __iter__(self):
            return map(lambda x:Bible.Chapter(self.id,x+1,self.bible),range(len(self)))
        
        def __repr__(self):
            return f'<Bible.Book({self.id})>'


    class Chapter:
        """
        Represents a single chapter within a Bible book.

        A chapter's content is fetched from bible.com upon initialization.
        It parses the HTML content to extract all verses and their text.
        The class handles potentially complex HTML structures to correctly
        identify verse numbers and aggregate their content.

        Verse extraction logic involves:
        - Searching for a JSON-like 'content' string within the page source.
        - Parsing the HTML content of this string.
        - Iterating through specific <span> tags to find verse text.
        - Using helper functions (`findVerseParent`, `findMinVerse`) to
          accurately determine verse numbers, especially when verse markers
          are not on the immediate parent or indicate ranges.

        Attributes:
            book (str): The USFM identifier of the parent book.
            chapter (int): The chapter number.
            bible (int): The ID of the parent Bible version.
            verses (defaultdict(str)): A dictionary mapping verse numbers
                                               to their text content.
        """
        def __init__(self,book:str,chapter:int,bible_id:int):
            def findVerseParent(text_tag):
                try:
                    while True:
                        verse_class = text_tag.attrib['class']
                        if verse_class.startswith('verse v'):
                            return text_tag
                        text_tag = text_tag.getparent()
                except:
                    if text_tag.text.strip()!="":
                        print(text_tag.text, text_tag.attrib)
                    raise
                return 0

            def findMinVerse(verse):
                verse = verse.replace('verse ','')
                verse = verse.replace('v','')
                return min(int(x) for x in verse.split(' '))
            
            self.book = book
            self.chapter = chapter
            self.bible = bible_id 
            self.verses = defaultdict(str)

            url = f'https://www.bible.com/bible/{bible_id}/{book}.{chapter}'
            res = utils.getResponse(url)
            pattern = re.compile(r'"content":".*?\\u003e"')
            try:
                str_html = utils.decodeHtml(pattern.search(res.text,120000)[0][11:-1])
            except Exception as e:
                print('error',url)
                raise
            etree = html.fromstring(str_html)
            last_verse = ''
            
            for i in etree.xpath('//span/span[@class="content"]'):
                parent = i.getparent() 
                vCount = parent.attrib['class'].count('v')
                
                if vCount<2:
                    parent = findVerseParent(parent)
                    vCount = parent.attrib['class'].count('v')
                
                if vCount>2:
                    verse = findMinVerse(parent.attrib['class'])
                else:
                    verse = int(parent.attrib['class'].replace('verse v',''))

                self.verses[verse]+= ' '+i.text.strip() if last_verse == verse else i.text.strip()
                    
                last_verse = verse

        def __getitem__(self,key):
            return self.verses[key]
        
        def __iter__(self):
            return iter(self.verses)

        def __len__(self):
            return len(self.verses)
        
        def __repr__(self):
            return f'<Bible.Chapter({self.book}.{self.chapter})>'

        def get_verse(self,verse:int=None):
            if verse is None:
                return self.verses
            return self.verses[verse]