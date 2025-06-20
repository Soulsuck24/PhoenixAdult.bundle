"""googlesearch is a Python library for searching Google, easily."""

from time import sleep
try:
    from bs4 import BeautifulSoup
    is_bs4 = True
except ImportError:
    from BeautifulSoup import BeautifulSoup
    is_bs4 = False
from requests import get
from .user_agents import get_useragent
from urllib import unquote


def _req(query, site, results, lang, start, proxies, timeout, ssl_verify, region):
    resp = get(
        url='https://www.google.com/search',
        headers={
            'User-Agent': get_useragent(),
            'Accept': '*/*'
        },
        params={
            'q': query,
            'num': results + 2,  # Prevents multiple requests
            'hl': lang,
            'start': start,
            'safe': 'off',
            'as_sitesearch': site,
            'gl': region,
        },
        proxies=proxies,
        timeout=timeout,
        verify=ssl_verify,
        cookies={
            'CONSENT': 'PENDING+987', # Bypasses the consent page
            'SOCS': 'CAESHAgBEhIaAB'
        }
    )
    resp.raise_for_status()
    return resp


class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return 'SearchResult(url={url}, title={title}, description={description})'.format(url=self.url, title=self.title, description=self.description)


def search(term, site, num_results=10, lang='en', proxy=None, advanced=False, sleep_interval=0, timeout=5, ssl_verify=None, region=None, start_num=0, unique=False):
    """Search the Google search engine"""

    # Proxy setup
    proxies = {'https': proxy, 'http': proxy} if proxy and (proxy.startswith('https') or proxy.startswith('http') or proxy.startswith('socks5')) else None

    start = start_num
    fetched_results = 0  # Keep track of the total fetched results
    fetched_links = set() # to keep track of links that are already seen previously

    # Fetch
    while fetched_results < num_results:
        # Send request
        resp = _req(term, site, num_results - start, lang, start, proxies, timeout, ssl_verify, region)

        # put in file - comment for debugging purpose
        # with open('google.html', 'w') as f:
        #     f.write(resp.text)
        
        # Parse
        if is_bs4:
            soup = BeautifulSoup(resp.text, 'html.parser')
        else:
            soup = BeautifulSoup(resp.text)
        result_block = soup.findAll('div', attrs={'class': 'ezO2md'})
        new_results = 0  # Keep track of new results in this iteration

        for result in result_block:
            # Find the link tag within the result block
            link_tag = result.find('a', href=True)
            # Find the title tag within the link tag
            title_tag = link_tag.find('span', class_='CVA68e') if link_tag else None
            # Find the description tag within the result block
            description_tag = result.find('span', class_='FrIlee')

            # Check if all necessary tags are found
            if link_tag and title_tag and description_tag:
                # Extract and decode the link URL
                link = unquote(link_tag['href'].split('&')[0].replace('/url?q=', '')) if link_tag else ''
            # Extract and decode the link URL
            link = unquote(link_tag['href'].split('&')[0].replace('/url?q=', '')) if link_tag else ''
            # Check if the link has already been fetched and if unique results are required
            if link in fetched_links and unique:
                continue  # Skip this result if the link is not unique
            # Add the link to the set of fetched links
            fetched_links.add(link)
            # Extract the title text
            title = title_tag.text if title_tag else ''
            # Extract the description text
            description = description_tag.text if description_tag else ''
            # Increment the count of fetched results
            fetched_results += 1
            # Increment the count of new results in this iteration
            new_results += 1
            # Yield the result based on the advanced flag
            if advanced:
                yield SearchResult(link, title, description)  # Yield a SearchResult object
            else:
                yield link  # Yield only the link

            if fetched_results >= num_results:
                break  # Stop if we have fetched the desired number of results

        if new_results == 0:
            #If you want to have printed to your screen that the desired amount of queries can not been fulfilled, uncomment the line below:
            #print('Only {fetched_results} results found for query requiring {num_results} results. Moving on to the next query.'.format(fetched_results=fetched_results, num_results=num_results)
            break  # Break the loop if no new results were found in this iteration

        start += 10  # Prepare for the next set of results
        sleep(sleep_interval)
