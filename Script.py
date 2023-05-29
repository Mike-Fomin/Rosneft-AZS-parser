import concurrent.futures
from itertools import chain

import requests
from bs4 import BeautifulSoup

# function prints and returns the list of regions in format: "name - code"
def get_regions(url: str) -> dict[str, int]:
    regions_dict = {}
    f_response = requests.get(url).text
    f_soup = BeautifulSoup(markup=f_response, features='lxml')
    f_block = f_soup.find(name="div", class_="row t-2 clearfix m_b1")
    f_regions = f_block.find("div", class_="cell s-3").find_all("option")
    for r in f_regions:
        print(f"{r.text.strip()} - {r['value']}")
        regions_dict[r.text.strip()] = int(r['value'])
    return regions_dict


# func for parse addresses
def azs_address(url: str, params: dict[str, int], page: int) -> list[str]:
    params = {"page": page} | params
    get_response = requests.get(url, params=params).text
    soup_func = BeautifulSoup(markup=get_response, features="lxml")

    # find the block with addresses
    block = soup_func.find("div", class_="azs-list")
    addresses = block.find_all("div", class_="cell s-3")

    # return addresses from the block
    return [adr.text for adr in addresses if addresses.count(adr) == 1]


def main():
    cur_url = "https://www.rosneft-azs.ru/Spisok-AZS?"
    regions = get_regions(cur_url)

    while True:
        print()
        region_number = int(input("Choose the code of region in the list or '-1' for all regions: "))
        if region_number not in regions.values():
            print("Invalid code. Try again.")
        else:
            break

    cur_params = {"brand": -1, "region": region_number}
    print("addresses list is creating, it takes time...")

    # find the number of pages
    response = requests.get(cur_url, params=cur_params).text
    soup = BeautifulSoup(markup=response, features="lxml")
    pages_count_block = soup.find(name="div", class_="pagination font_16 m_b2")
    pages_count = pages_count_block.find_all(name="div", class_="pagination__page")
    max_page = int(pages_count[-1].text.strip())

    # connect multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_page) as executor:
        futures = [executor.submit(azs_address, cur_url, cur_params, i) for i in range(1, max_page + 1)]

    # write data to file
    with open("azs_list.txt", "w", encoding="utf-8") as file:
        for i, val in enumerate(chain.from_iterable(map(lambda x: x.result(), futures)), 1):
            file.write(f"{i}) {val}\n")

    print("Complete!")


if __name__ == "__main__":
    main()
