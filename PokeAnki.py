import csv
import os

import genanki as genanki
import requests
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
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
    url = f"https://pokemondb.net/pokedex/{name.lower()}"
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

    if form:  # If the Pokémon is an alternate form
        if len(abilities_rows) == 2:
            abilities_row = abilities_rows[
                1]  # Use the second set for alternate forms if only one alternate form is present
        elif len(abilities_rows) == 3:
            # For Pokémon with two Mega forms, determine which set to use based on the form
            if 'X' in form:
                abilities_row = abilities_rows[1]  # Second occurrence for Mega X
            elif 'Y' in form:
                abilities_row = abilities_rows[2]  # Third occurrence for Mega Y
            elif 'Alolan' in form:
                abilities_row = abilities_rows[1] # Basically just for Meowth
            elif 'Galarian' in form:
                abilities_row = abilities_rows[2]
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
    base_url = "https://projectpokemon.org/home/docs/spriteindex_148/switch-sv-style-sprites-for-home-r153/"
    sprite_folder = "Files/Sprites"

    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    name = pokemon['Name']
    number = pokemon['Number'].zfill(4)
    form = pokemon['Form']

    all_forms = [p for p in pokemon_data if p['Name'] == name]
    current_form_index = all_forms.index(pokemon)

    if len(all_forms) > 1 and form != '':
        alt_form_suffix = f"_{current_form_index:02}"
        filename = f"{number}{alt_form_suffix}.png"
    else:
        filename = f"{number}.png"

    img_tag = soup.find('img', alt=f"{filename}")

    if img_tag:
        image_url = img_tag['src']
        response = requests.get(image_url)
        if response.status_code == 200:
            path = f"Files/Sprites/{filename}"
            with open(path, 'wb') as f:
                f.write(response.content)
            return path

    return None

def download_cry(pokemon):
    cry_url = "https://play.pokemonshowdown.com/audio/cries/"
    response = requests.get(cry_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    name = pokemon['Name'].lower().replace(' ', '')
    form = pokemon['Form']


    if 'Mega' in form:
        if 'X' in form:
            filename = f"{name}-megax.mp3"
        elif 'Y' in form:
            filename = f"{name}-megay.mp3"
        else:
            filename = f"{name}-mega.mp3"
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
    # Convert stats to integers for plotting
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
    colors = []
    for stat in stats:
        if stat < 60:
            colors.append('#ff7f0f')
        elif 60 <= stat < 80:
            colors.append('#ffdd57')
        elif 80 <= stat < 100:
            colors.append('#ffdd57')
        elif 100 <= stat < 120:
            colors.append('#a0e515')
        elif 120 <= stat < 140:
            colors.append('#1fb553')
        else:
            colors.append('#00c2b8')


    fig, ax = plt.subplots()
    y_positions = range(len(stats))

    bars = ax.barh(y_positions, stats, color=colors, align='center', height=0.6, edgecolor='none', linewidth=0)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # Invert the y-axis to have the first entry at the top

    ax.xaxis.set_major_formatter(plt.NullFormatter())


    for bar, value in zip(bars, stats):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' {value}', va='center', ha='left', color='black', fontweight='normal')

    plt.tight_layout(pad=3.0)
    max_stat = max(stats)
    padding = max_stat * 0.1
    ax.set_xlim(0, max_stat + padding)

    bst = sum(stats)

    plt.title(f"(BST: {bst})", size=16)
    plt.savefig(f"Files/BST/{filename}")
    plt.close()

    return (f"Files/BST/{filename}")

def get_absolute_media_path(relative_path):
    # Ensure the path uses forward slashes for compatibility
    normalized_path = relative_path.replace('\\', '/')
    # Construct an absolute path
    return os.path.abspath(normalized_path)

def create_pokemon_anki(pokemon_data):
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

    deck = genanki.Deck(
        696969420,
        'Deckaroni'
    )

    media_files = []

    for x in range(0, 203):
        pokemon = pokemon_data[x]
        # Assuming scrape_pokemon_details, download_pokemon_sprite, download_cry, and create_base_stat_graph are defined
        classification, abilities = scrape_pokemon_details(pokemon)
        sprite_path = download_pokemon_sprite(pokemon).replace('\\', '/')
        cry_path = download_cry(pokemon).replace('\\', '/')
        graph_path = create_base_stat_graph(pokemon).replace('\\', '/')  # Ensure this function returns the graph path

        # Prepare typing images (ensure these images exist in your media folder)
        type1_image = f"Files/Types/{pokemon['Type 1']}.png".replace('\\', '/')
        type2_image = f"Files/Types/{pokemon['Type 2']}.png".replace('\\', '/') if pokemon['Type 2'] else ""

        if sprite_path:
            sprite_path_abs = get_absolute_media_path(sprite_path)
            if os.path.exists(sprite_path_abs) and sprite_path_abs not in media_files:
                media_files.append(sprite_path_abs)

        if cry_path:
            cry_path_abs = get_absolute_media_path(cry_path)
            if os.path.exists(cry_path_abs) and cry_path_abs not in media_files:
                media_files.append(cry_path_abs)

        if graph_path:
            graph_path_abs = get_absolute_media_path(graph_path)
            if os.path.exists(graph_path_abs) and graph_path_abs not in media_files:
                media_files.append(graph_path_abs)

        if type1_image:
            type1_image_abs = get_absolute_media_path(type1_image)
            if os.path.exists(type1_image_abs) and type1_image_abs not in media_files:
                media_files.append(type1_image_abs)

        if type2_image:
            type2_image_abs = get_absolute_media_path(type2_image)
            if os.path.exists(type2_image_abs) and type2_image_abs not in media_files:
                media_files.append(type2_image_abs)


        # Add paths to media_files if not already included
        # for path in [sprite_path, cry_path, graph_path, type1_image, type2_image]:
        #     full_path = os.path.abspath(path)  # Convert to absolute path for verification
        #     if path and os.path.exists(full_path) and path not in media_files:
        #         media_files.append(path)

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
        deck.add_note(note)
        temp = pokemon['Name'] if (pokemon['Form'] == '') else (pokemon['Form'])
        print(f"Pokemon Added: #{pokemon['Number']} {temp}")


        # Create the Anki package with media files
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file('pokemon_deck.apkg')

all_forms = [p for p in pokemon_data if p['Name'] == 'Calyrex']
index = pokemon_data.index(all_forms[2])
poketest = pokemon_data[index]
# classification, abilities = scrape_pokemon_details(poketest)
# print(poketest['Name']) if (poketest['Form'] == '') else print(poketest['Form'])
# print(classification, abilities)
# print(pokemon_data)
# create_base_stat_graph(pokemon_data[8])
#
print(download_pokemon_sprite(poketest))
# print(download_cry(pokemon_data[7]))

# print(pokemon_data)

create_pokemon_anki(pokemon_data)
