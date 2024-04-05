import csv
import os

import genanki as genanki
import requests
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import numpy as np

pokemon_data = []

with open('Files/pokemon.txt', 'r') as file:
    reader = csv.DictReader(file);
    for row in reader:
        pokemon_data.append(row);

def scrape_pokemon_details(pokemon):
    name = pokemon['Name']
    form = pokemon['Form']
    url = f"https://pokemondb.net/pokedex/{name.lower().replace(' ', '-').replace('.', '')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    classification_row = soup.find('th', string='Species')
    if classification_row:
        classification = classification_row.find_next_sibling('td').text
    else:
        classification = "Not found"

    # Try to find the paragraph with generation info more flexibly
    paragraphs = soup.find_all('p')
    gen_info_text = None
    for paragraph in paragraphs:
        if 'introduced in' in paragraph.text:
            gen_info_text = paragraph.find('abbr').text if paragraph.find('abbr') else None
            break

    if gen_info_text:
        classification += f" | {gen_info_text}"  # Append the generation info to the classification

    abilities_rows = soup.find_all('th', string='Abilities')
    abilities = []

    all_forms = [p for p in pokemon_data if p['Name'] == name]
    current_form_index = all_forms.index(pokemon)

    if form:  # If the Pokémon is an alternate form
        if len(abilities_rows) > 1:
            abilities_row = abilities_rows[current_form_index]
        # if len(abilities_rows) == 2:
        #     abilities_row = abilities_rows[
        #         1]  # Use the second set for alternate forms if only one alternate form is present
        # elif len(abilities_rows) == 3:
        #     # For Pokémon with two Mega forms, determine which set to use based on the form
        #     if 'X' in form:
        #         abilities_row = abilities_rows[1]  # Second occurrence for Mega X
        #     elif 'Y' in form:
        #         abilities_row = abilities_rows[2]  # Third occurrence for Mega Y
        #     elif 'Alolan' in form:
        #         abilities_row = abilities_rows[1] # Basically just for Meowth
        #     elif 'Galarian' in form:
        #         abilities_row = abilities_rows[2]
        else:
            abilities_row = abilities_rows[0]  # Default to the first set if conditions don't match
    else:
        abilities_row = abilities_rows[0]  # Use the first set for the base form
    if abilities_row:
        abilities_td = abilities_row.find_next_sibling('td')
        for a in abilities_td.find_all('a'):
            ability_name = a.text

            # Check if the current ability is a hidden ability
            # We check if the parent of the <a> tag is a <small> tag with class 'text-muted'
            if a.find_parent('small', class_='text-muted'):
                ability_name += ' (H)'  # Mark as hidden ability

            abilities.append(ability_name)
    else:
        abilities = ["Not found"]

    return classification, abilities

def download_pokemon_sprite(pokemon):
    # base_url = "https://projectpokemon.org/home/docs/spriteindex_148/switch-sv-style-sprites-for-home-r153/"
    # sprite_folder = "Files/Sprites"
    #
    # response = requests.get(base_url)
    # soup = BeautifulSoup(response.content, 'html.parser')
    #
    # name = pokemon['Name']
    # number = pokemon['Number'].zfill(4)
    # form = pokemon['Form']
    #
    # all_forms = [p for p in pokemon_data if p['Name'] == name]
    # current_form_index = all_forms.index(pokemon)
    #
    # if len(all_forms) > 1 and form != '':
    #     alt_form_suffix = f"_{current_form_index:02}"
    #     filename = f"{number}{alt_form_suffix}.png"
    # else:
    #     filename = f"{number}.png"
    #
    # img_tag = soup.find('img', alt=f"{filename}")
    #
    # if img_tag:
    #     image_url = img_tag['src']
    #     response = requests.get(image_url)
    #     if response.status_code == 200:
    #         path = f"Files/Sprites/{filename}"
    #         with open(path, 'wb') as f:
    #             f.write(response.content)
    #         return path
    #
    # return None

    # New base URL format
    name = pokemon['Name'].lower().replace(' ', '-').replace('.', '')
    url = f"https://pokemondb.net/pokedex/{name}"

    response = requests.get(url)
    if response.status_code != 200:
        return None  # Could not fetch the page

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all img tags within the artwork section
    img_tags = soup.find_all('img', alt=lambda alt: alt and 'artwork' in alt)

    # If there are multiple forms, ensure we only consider unique artworks for each form
    all_forms = [p for p in pokemon_data if p['Name'].lower() == pokemon['Name'].lower()]
    current_form_index = all_forms.index(pokemon)

    if len(all_forms) > 1:
        filename_suffix = f"_{current_form_index:02}"
    else:
        filename_suffix = ''

    # Safety check to avoid index out of range
    if current_form_index < len(img_tags):
        image_url = img_tags[current_form_index]['src']

        filename = f"{pokemon['Number'].zfill(4)}{filename_suffix}.jpg"
        path = f"Files/Sprites/{filename}"

        # Download and save the image
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return path
    return None

def download_cry(pokemon):
    cry_url = "https://play.pokemonshowdown.com/audio/cries/"
    response = requests.get(cry_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    name = pokemon['Name'].lower().replace(' ', '').replace('-', '').replace('\'', '').replace('.', '')
    form = pokemon['Form']

    all_forms = [p for p in pokemon_data if p['Name'] == pokemon['Name']]
    current_form_index = all_forms.index(pokemon)

    if current_form_index != 0:
        if 'Mega' in form:
            if 'X' in form:
                filename = f"{name}-megax.mp3"
            elif 'Y' in form:
                filename = f"{name}-megay.mp3"
            else:
                filename = f"{name}-mega.mp3"
        elif name == 'calyrex':
            if current_form_index == 1:
                filename = "calyrex-ice.mp3"
            elif current_form_index == 2:
                filename = "calyrex-shadow.mp3"
        elif 'Therian' in form:
            filename = f"{name}-therian.mp3"
        elif 'Eternamax' in form:
            filename = f"{name}-eternamax.mp3"
        elif name == 'gimmighoul':
            if current_form_index == 0:
                filename = "gimmighoul.mp3"
            elif current_form_index == 1:
                filename = "gimmighoul-roaming.mp3"
        elif 'Primal' in form:
            filename = f"{name}-primal.mp3"
        elif name == 'hoopa':
            if current_form_index == 0:
                filename = "hoopa.mp3"
            elif current_form_index == 1:
                filename = "hoopa-unbound.mp3"
        elif name == 'kyurem':
            if current_form_index == 1:
                filename = "kyurem-white.mp3"
            elif current_form_index == 2:
                filename = "kyurem-black.mp3"
        elif name == 'lycanroc':
            if current_form_index == 1:
                filename = "lycanroc-midnight.mp3"
            elif current_form_index == 2:
                filename = "lycanroc-dusk.mp3"
        elif name == 'necrozma':
            if current_form_index == 1:
                filename = "necrozma-dawnwings.mp3"
            elif current_form_index == 2:
                filename = "necrozma-duskmane.mp3"
            elif current_form_index == 3:
                filename = "necrozma-ultra.mp3"
        elif name == 'oricorio':
            if current_form_index == 1:
                filename = "oricorio-pompom.mp3"
            elif current_form_index == 2:
                filename = "oricorio-pau.mp3"
            elif current_form_index == 3:
                filename = "oricorio-sensu.mp3"
        elif name == "porygon-z":
            filename = "porygonz.mp3"
        elif name == "shaymin" and current_form_index == 1:
            filename = "shaymin-sky.mp3"
        elif name == 'tatsugiri':
            if current_form_index == 1:
                filename = "tatsugiri-droopy.mp3"
            elif current_form_index == 2:
                filename = "tatsugiri-stretchy.mp3"
        elif name == "toxtricity" and current_form_index == 1:
            filename = "toxtricity-lowkey.mp3"
        elif name == "urshifu" and current_form_index == 1:
            filename = "urshifu-rapidstrike.mp3"
        elif name == "wishiwashi" and current_form_index == 1:
            filename = "wishiwashi-school.mp3"
        elif 'Crowned' in form:
            filename = f"{name}-crowned.mp3"
        elif name == 'zygarde':
            if current_form_index == 1:
                filename = "zygarde-10.mp3"
            elif current_form_index == 2:
                filename = "zygarde-complete.mp3"
        else:
            filename = f"{name}.mp3"
    else:
        filename = f"{name}.mp3"

    a_tag = soup.find('a', href=True, string=filename)

    if a_tag:
        audio_url = cry_url + a_tag['href']

        audio_response = requests.get(audio_url)

        if audio_response.status_code == 200:
            path = f"Files/SoundCry/{filename}"
            with open(path, 'wb') as f:
                f.write(audio_response.content)
            return path

    return None


def create_base_stat_graph(pokemon):
    labels = np.array(['HP', 'Attack', 'Defense', 'Sp.Attack', 'Sp.Defense', 'Speed'])
    stats = np.array([int(pokemon['HP']), int(pokemon['Attack']), int(pokemon['Defense']),
                      int(pokemon['Sp.Attack']), int(pokemon['Sp.Defense']), int(pokemon['Speed'])])

    name = pokemon['Name']
    form = pokemon['Form']

    all_forms = [p for p in pokemon_data if p['Name'] == name]
    current_form_index = all_forms.index(pokemon)

    if len(all_forms) > 1 and form != '':
        alt_form_suffix = f"_{current_form_index:02}"
        filename = f"{name}{alt_form_suffix}.png"
    else:
        filename = f"{name}.png"

    colors = ['#ff7f0f' if stat < 60 else
              '#ffdd57' if stat < 90 else
              '#A0E515' if stat < 120 else
              '#23cd5e' if stat <= 140 else
              '#00c2b8' for stat in stats]

    fig, ax = plt.subplots(figsize=(9.5, 6))
    y_positions = np.arange(len(stats))[::-1]

    # Create rounded bars using FancyBboxPatch
    bar_height = 0.5
    max_bst_scale = 256
    stat_label_x_pos = max_bst_scale * 1.01
    for y_pos, stat, color in zip(y_positions, stats, colors):
        bar = FancyBboxPatch((0, y_pos - bar_height / 2), width=stat, height=bar_height,
                             boxstyle="round,pad=0.1,rounding_size=0.1",
                             edgecolor='black', facecolor=color, linewidth=1)
        ax.add_patch(bar)
        # text_pos = max(stat + 5, max_bst_scale * 0.03)  # Adjust text position for visibility
        # ax.text(text_pos, y_pos, f'{stat}', va='center', color='black', fontweight='normal')

        # right_align_text_pos = max_bst_scale * 0.98  # Adjust as needed for perfect alignment
        ax.text(stat_label_x_pos, y_pos, f'{stat}', va='center', ha='left', color='black', fontweight='normal', size=20)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=16)
    ax.invert_yaxis()

    ax.xaxis.set_major_formatter(plt.NullFormatter())
    ax.tick_params(bottom=False)  # Remove ticks at the bottom

    ax.set_ylim(-0.5, len(stats) - 0.5)
    plt.subplots_adjust(left=0.15, bottom=0.01, top=0.90)

    ax.set_xlim(0, max_bst_scale)

    bst = sum(stats)

    # Adjust title placement
    plt.title(f"BST: {bst}", size=28, pad=8)  # pad value might need adjustment

    plt.savefig(f"Files/BST/{filename}")
    plt.close()

    return f"Files/BST/{filename}"

def get_absolute_media_path(relative_path):
    # Ensure the path uses forward slashes for compatibility
    normalized_path = relative_path.replace('\\', '/')
    # Construct an absolute path
    return os.path.abspath(normalized_path)

def create_pokemon_anki(pokemon_data, input_gen):
    generation_ranges = {
        'Gen 1': (1, 151),
        'Gen 2': (152, 251),
        'Gen 3': (252, 386),
        'Gen 4': (387, 493),
        'Gen 5': (494, 649),
        'Gen 6': (650, 721),
        'Gen 7': (722, 809),
        'Gen 8': (810, 905),
        'Gen 9': (906, 1025),
    }


    # Get note html and css
    with open('Files/styling.css', 'r') as file:
        styling = file.read()
    with open('Files/front.html', 'r', encoding='utf-8') as file:
        front = file.read()
    with open('Files/back.html', 'r', encoding='utf-8') as file:
        back = file.read()

    model = genanki.Model(
        420696969,
        'Pokemon Model',
        fields=[
            {'name': 'Pokemon'},
            {'name': 'Classification'},
            {'name': 'Dex#'},
            {'name': 'Abilities'},
            {'name': 'BST'},
            {'name': 'SoundCry'},
            {'name': 'Sprite'},
            {'name': 'Type1'},
            {'name': 'Type2'},
            {'name': 'Extra Info'}
        ],
        templates=[
            {
                'name': 'Cardaroni',
                'qfmt': front,
                'afmt': back,
            },
        ],
        css = styling,
    )

    # deck = genanki.Deck(
    #     696969420,
    #     'Deckaroni'
    # )
    generation_decks = {gen: genanki.Deck(16000000 + idx, f"{gen} Deck") for idx, gen in enumerate(generation_ranges)}

    def find_generation(pokedex_number):
        for gen, (start, end) in generation_ranges.items():
            if start <= pokedex_number <= end:
                return gen
        return None

    media_files = []

    for pokemon in pokemon_data:
        pokemon_number = int(pokemon['Number'])
        gen = find_generation(pokemon_number)
        if gen == input_gen:
            # Assuming scrape_pokemon_details, download_pokemon_sprite, download_cry, and create_base_stat_graph are defined
            classification, abilities = scrape_pokemon_details(pokemon)
            sprite_path = download_pokemon_sprite(pokemon).replace('\\', '/')
            cry_path = download_cry(pokemon).replace('\\', '/')
            graph_path = create_base_stat_graph(pokemon).replace('\\', '/')  # Ensure this function returns the graph path

            # Prepare typing images (ensure these images exist in your media folder)
            type1_image = f"Files/Types/{pokemon['Type 1']}.png".replace('\\', '/')
            type2_image = f"Files/Types/{pokemon['Type 2']}.png".replace('\\', '/') if pokemon['Type 2'] else ""

            pokemon_name = pokemon['Name']
            form = pokemon['Form']
            if form:
                pokemon_name = form

            # Create the note
            note = genanki.Note(
                model=model,
                fields=[
                    pokemon_name,
                    classification,
                    pokemon['Number'],
                    ', '.join(abilities),  # Convert list of abilities to a string
                    f'<img src="{os.path.basename(graph_path)}">',
                    f'[sound:{os.path.basename(cry_path)}]',
                    f'<img src="{os.path.basename(sprite_path)}">',
                    f'<img src="{os.path.basename(type1_image)}">',
                    f'<img src="{os.path.basename(type2_image)}">' if type2_image else '',
                    '',
                ])

            # Add note to deck
            generation_decks[gen].add_note(note)
            temp = pokemon['Name'] if (pokemon['Form'] == '') else (pokemon['Form'])
            print(f"Pokemon Added: #{pokemon['Number']} {temp}")
            print(gen)
            print(pokemon)


        # Create the Anki package with media files
    for gen, deck in generation_decks.items():
        package = genanki.Package(deck)
        package.media_files = media_files  # Assuming you have a list of media files
        package.write_to_file(f'{gen}_pokemon_deck.apkg')




# print(pokemon_data)


# all_forms = [p for p in pokemon_data if p['Name'] == 'Mime Jr.']
# print(all_forms)
# for form in all_forms:
#     index = pokemon_data.index(form)
#     poketest = pokemon_data[index]
#     print("Name: " + poketest['Name']) if (poketest['Form'] == '') else print(poketest['Form'])
#     classification, abilities = scrape_pokemon_details(poketest)
#     print(abilities)
#     print(create_base_stat_graph(poketest))
#     print(download_pokemon_sprite(poketest))
#     print(download_cry(poketest))
#


create_pokemon_anki(pokemon_data, 'Gen 1')
