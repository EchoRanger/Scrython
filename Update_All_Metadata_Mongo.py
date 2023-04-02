import pymongo
import scrython
import requests
from bson.binary import Binary

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client["MtG_Collection"]
collection = db["Inventory"]
images_collection = db["Inventory_Images"]

for document in collection.find():
    card_name = document['Card Name']
    try:
        card = scrython.cards.Named(fuzzy=card_name)
    except Exception:
        try:
            card_name = card_name.split(" //")[0]
            card = scrython.cards.Named(fuzzy=card_name)
        except Exception:
            print(f"Card not found: {card_name}")
            continue

    if card.layout() in ('transform', 'modal_dfc', 'split', 'adventure', 'flip'):
        card_faces = card.card_faces()
        rules_text = f"{card_faces[0]['name']}:\n{card_faces[0]['oracle_text']}\n\n{card_faces[1]['name']}:\n{card_faces[1]['oracle_text']}"
        mana_cost = f"{card_faces[0]['mana_cost']} // {card_faces[1]['mana_cost']}"

        card_data = {
            'Rules Text': rules_text,
            'Mana Cost': mana_cost,
            'CMC': card.cmc(),
            'Type Line': card.type_line(),
            'Color Identity': card.color_identity(),
            'Set Code': card.set_code().upper(),
            'Set Name': card.set_name(),
            'Rarity': card.rarity(),
            'Artist': card.artist(),
            'Collector Number': card.collector_number(),
            'Border Color': card.border_color(),
            'Layout': card.layout(),
            'Name': card_faces[0]['name'],
            'Type': card_faces[0]['type_line'],
            'Power': card_faces[0]['power'] if 'Creature' in card_faces[0]['type_line'] else None,
            'Toughness': card_faces[0]['toughness'] if 'Creature' in card_faces[0]['type_line'] else None,
            'Loyalty': card_faces[0]['loyalty'] if 'Planeswalker' in card_faces[0]['type_line'] else None,
            'Face 2 Name': card_faces[1]['name'],
            'Face 2 Type': card_faces[1]['type_line'],
            'Face 2 Power': card_faces[1]['power'] if 'Creature' in card_faces[1]['type_line'] else None,
            'Face 2 Toughness': card_faces[1]['toughness'] if 'Creature' in card_faces[1]['type_line'] else None,
            'Face 2 Loyalty': card_faces[1]['loyalty'] if 'Planeswalker' in card_faces[1]['type_line'] else None,
        }

    else:
        rules_text = card.oracle_text()
        mana_cost = card.mana_cost()

        card_data = {
            'Rules Text': rules_text,
            'Mana Cost': mana_cost,
            'CMC': card.cmc(),
            'Type_Line': card.type_line(),
            'Color_Identity': card.color_identity(),
            'Set Code': card.set_code().upper(),
            'Set Name': card.set_name(),
            'Rarity': card.rarity(),
            'Artist': card.artist(),
            'Power': card.power() if 'Creature' in card.type_line() else None,
            'Toughness': card.toughness() if 'Creature' in card.type_line() else None,
            'Loyalty': card.loyalty() if 'Planeswalker' in card.type_line() else None,
            'Coector Number': card.collector_number(),
            'Border Color': card.border_color(),
            'Layout': card.layout()
        }

    # Update the document in the Inventory collection
    collection.update_one({'_id': document['_id']}, {'$set': card_data})


    # Download and store medium and cropped_art images
    medium_image_url = card.image_uris()['normal']
    cropped_art_image_url = card.image_uris()['art_crop']

    medium_image = requests.get(medium_image_url).content
    cropped_art_image = requests.get(cropped_art_image_url).content

    images_data = {
        "inventory_id": document["_id"],
        "medium_image": Binary(medium_image),
        "cropped_art_image": Binary(cropped_art_image)
    }
    images_collection.insert_one(images_data)