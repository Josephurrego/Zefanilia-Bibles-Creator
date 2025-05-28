from Bible import Bible
import os

def writeFile(bible:Bible):

    header = f"""<XMLBIBLE biblename="{bible.name}" revision="99" status="v" version="2.0.1.18" type="x-bible" p1:noNamespaceSchemaLocation="zef2005.xsd" xmlns:p1="http://www.w3.org/2001/XMLSchema-instance">
<INFORMATION>
<title>{bible.name}</title>
<creator/>
<subject/>
<identifier>{bible.abrev}</identifier>
<description>{bible.description}</description>
<publisher>{bible.author}</publisher>
<date/>
<language>{bible.lang.upper()}</language>
<type>Bible</type>
</INFORMATION>\n"""
    with open(f'Bibles/{bible.abrev}.xml','w',encoding='utf-8') as file:
        file.write(header)
        for idx,book in enumerate(bible,1):
            file.write(' '*2+f'<BIBLEBOOK bnumber="{idx}" bname="{book.name}" bsname="{book.abrev}">\n')
            chapters = bible[book].get_async_chapters()
            for chapter in chapters:
                file.write(' '*4+f'<CHAPTER cnumber="{chapter}">\n')
                for verse in chapters[chapter]:
                    file.write(' '*6+f' <VERS vnumber="{verse}">{chapters[chapter][verse]}</VERS>\n')
                file.write(' '*4+f'</CHAPTER>\n')
            file.write(' '*2+f'</BIBLEBOOK>\n')
            print(f'\t{book.name}✔')
        file.write('</XMLBIBLE>')

def writeBible(*bibles_id):
    """Writes Bibles, obtained from bible.com, into Zefanilia XML format.

    This function iterates through one or more provided Bible version IDs,
    fetches the data for each Bible using the `Bible` class, and then
    write the XML file in the Bibles folder.

    Arguments:
        *bibles_id (int): A variable number of Bible version IDs. Each ID is used to identify and fetch a specific Bible version from bible.com.

    Returns:
    None
    """
    os.makedirs('Bibles',exist_ok=True) # Create Bibles Dir
    print('**Starting**')
    for i in bibles_id:
        bible = Bible(i)
        print(f'{bible.name}({bible.abrev})')
        writeFile(bible)

