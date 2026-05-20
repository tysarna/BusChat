from django.core.management.base import BaseCommand
from restaurant.models import MenuItem


MENU_DATA = [
    # Appetizers
    {'name': 'Hummus Trio', 'category': 'appetizer', 'price': '9.95',
     'is_vegan': True, 'is_gluten_free': True, 'allergens': 'sesame',
     'description': 'House-made classic, roasted red pepper, and black olive hummus served with warm pita and fresh crudités.'},
    {'name': 'Falafel Bites (6pc)', 'category': 'appetizer', 'price': '8.95',
     'is_vegan': True, 'allergens': 'sesame, gluten',
     'description': 'Crispy golden falafel with tahini dipping sauce and pickled turnips.'},
    {'name': 'Stuffed Grape Leaves (5pc)', 'category': 'appetizer', 'price': '8.50',
     'is_vegan': True, 'is_gluten_free': True,
     'description': 'Tender vine leaves filled with spiced rice, pine nuts, and currants, served cold with lemon.'},
    {'name': 'Spanakopita (2pc)', 'category': 'appetizer', 'price': '7.95',
     'is_vegetarian': True, 'allergens': 'gluten, dairy, eggs',
     'description': 'Flaky phyllo triangles filled with spinach and feta, baked golden brown.'},
    {'name': 'Calamari Fritti', 'category': 'appetizer', 'price': '11.95',
     'allergens': 'gluten, shellfish',
     'description': 'Lightly breaded baby squid fried crispy, served with marinara and lemon aioli.'},
    # Mains
    {'name': 'Lamb Shawarma Plate', 'category': 'main', 'price': '17.95',
     'is_gluten_free': True, 'allergens': 'dairy',
     'description': 'Slow-roasted spiced lamb over saffron rice with grilled vegetables and creamy tzatziki.'},
    {'name': 'Chicken Shawarma Plate', 'category': 'main', 'price': '15.95',
     'is_gluten_free': True, 'allergens': 'dairy',
     'description': 'Marinated rotisserie chicken over saffron rice with grilled vegetables and garlic sauce.'},
    {'name': 'Falafel Pita Wrap', 'category': 'main', 'price': '12.95',
     'is_vegan': True, 'allergens': 'gluten, sesame',
     'description': 'Three crispy falafel in warm pita with hummus, pickled cabbage, tomato, and tahini.'},
    {'name': 'Grilled Salmon', 'category': 'main', 'price': '22.95',
     'is_gluten_free': True, 'allergens': 'fish',
     'description': 'Atlantic salmon with chermoula herb crust, roasted lemon, and tabbouleh salad.'},
    {'name': 'Moussaka', 'category': 'main', 'price': '16.95',
     'allergens': 'gluten, dairy, eggs',
     'description': 'Classic layered eggplant and spiced ground beef with creamy béchamel, baked to order.'},
    {'name': 'Vegetarian Moussaka', 'category': 'main', 'price': '14.95',
     'is_vegetarian': True, 'allergens': 'gluten, dairy, eggs',
     'description': 'Layered roasted eggplant, lentils, and spiced chickpeas with béchamel.'},
    {'name': 'Mixed Grill Platter', 'category': 'main', 'price': '24.95',
     'is_gluten_free': True,
     'description': 'Lamb kofta, chicken skewer, and beef kebab over saffron rice with grilled peppers and pita.'},
    {'name': 'Shrimp Saganaki', 'category': 'main', 'price': '19.95',
     'is_gluten_free': True, 'allergens': 'shellfish, dairy',
     'description': 'Gulf shrimp in spiced tomato-feta sauce, finished with ouzo, served with crusty bread.'},
    # Sides
    {'name': 'Saffron Rice', 'category': 'side', 'price': '3.95',
     'is_vegan': True, 'is_gluten_free': True, 'allergens': 'tree nuts',
     'description': 'Fragrant basmati rice with saffron, golden raisins, and toasted almonds.'},
    {'name': 'Greek Salad', 'category': 'side', 'price': '7.95',
     'is_vegetarian': True, 'is_gluten_free': True, 'allergens': 'dairy',
     'description': 'Tomato, cucumber, olives, red onion, pepperoncini, and large-cut feta with oregano vinaigrette.'},
    {'name': 'Tabbouleh', 'category': 'side', 'price': '5.95',
     'is_vegan': True, 'allergens': 'gluten',
     'description': 'Fine bulgur with masses of fresh parsley, mint, tomato, lemon, and olive oil.'},
    {'name': 'Pita Bread (2pc)', 'category': 'side', 'price': '2.95',
     'is_vegan': True, 'allergens': 'gluten',
     'description': 'Warm house-baked pita, plain or sesame upon request.'},
    {'name': 'Tzatziki', 'category': 'side', 'price': '4.95',
     'is_vegetarian': True, 'is_gluten_free': True, 'allergens': 'dairy',
     'description': 'Thick Greek yogurt with cucumber, garlic, and dill, served with pita.'},
    # Desserts
    {'name': 'Baklava (3pc)', 'category': 'dessert', 'price': '6.95',
     'is_vegetarian': True, 'allergens': 'gluten, tree nuts, dairy',
     'description': 'Layers of crispy phyllo, walnuts, and honey syrup with rose water.'},
    {'name': 'Kunafa', 'category': 'dessert', 'price': '8.95',
     'is_vegetarian': True, 'allergens': 'gluten, dairy',
     'description': 'Warm shredded wheat pastry filled with melted Nabulsi cheese and sweet sugar syrup.'},
    {'name': 'Chocolate Tahini Cake', 'category': 'dessert', 'price': '7.95',
     'is_vegetarian': True, 'is_gluten_free': True, 'allergens': 'sesame, dairy, eggs',
     'description': 'Dense flourless chocolate cake with tahini swirl and sesame brittle.'},
    {'name': 'Muhallabia', 'category': 'dessert', 'price': '5.95',
     'is_vegetarian': True, 'is_gluten_free': True, 'allergens': 'dairy, tree nuts',
     'description': 'Chilled milk pudding with orange blossom water, pistachios, and dried rose petals.'},
    # Drinks
    {'name': 'Mint Lemonade', 'category': 'drink', 'price': '4.50',
     'is_vegan': True, 'is_gluten_free': True,
     'description': 'Fresh-squeezed lemon with muddled mint and a hint of orange blossom water.'},
    {'name': 'Ayran', 'category': 'drink', 'price': '3.50',
     'is_vegetarian': True, 'is_gluten_free': True, 'allergens': 'dairy',
     'description': 'Chilled savory yogurt drink with a pinch of dried mint — a refreshing classic.'},
    {'name': 'Turkish Coffee', 'category': 'drink', 'price': '3.95',
     'is_vegan': True, 'is_gluten_free': True,
     'description': 'Rich traditional coffee brewed in a cezve, served with lokum (Turkish delight).'},
    {'name': 'House Iced Tea', 'category': 'drink', 'price': '2.95',
     'is_vegan': True, 'is_gluten_free': True,
     'description': 'Hibiscus and apple iced tea, lightly sweetened and served over ice.'},
]


class Command(BaseCommand):
    help = 'Seed the database with Zara\'s Mediterranean Kitchen menu data'

    def handle(self, *args, **options):
        created_count = 0
        for item_data in MENU_DATA:
            defaults = {
                'description': item_data.get('description', ''),
                'price': item_data['price'],
                'is_vegetarian': item_data.get('is_vegetarian', False),
                'is_vegan': item_data.get('is_vegan', False),
                'is_gluten_free': item_data.get('is_gluten_free', False),
                'is_spicy': item_data.get('is_spicy', False),
                'allergens': item_data.get('allergens', ''),
                'is_available': True,
            }
            if item_data.get('is_vegan'):
                defaults['is_vegetarian'] = True
            _, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                category=item_data['category'],
                defaults=defaults,
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded menu: {created_count} new items created, {len(MENU_DATA)} total items in DB.'
        ))
