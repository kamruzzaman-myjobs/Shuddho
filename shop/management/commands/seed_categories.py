"""
Standard Category -> Sub-category -> Sub-sub-category seed script.

কোথায় রাখবে:
    shop/management/commands/seed_categories.py

চালানোর নিয়ম:
    python manage.py seed_categories

এই script বারবার চালালেও সমস্যা নেই (get_or_create ব্যবহার করা হয়েছে),
already থাকা category duplicate হবে না।
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shop.models import Category


# ================= CATEGORY DATA =================
# Format:  "Top Category": { "Sub Category": ["Sub-sub-1", "Sub-sub-2", ...], ... }

# CATEGORY_DATA = {
#     "Food": {
#         "Grocery": ["Rice & Flour", "Oil & Ghee", "Spices & Herbs", "Pulses & Lentils"],
#         "Snacks": ["Chips & Chanachur", "Biscuits & Cookies", "Chocolates & Candy", "Bakery Items"],
#         "Beverages": ["Soft Drinks", "Tea & Coffee", "Juice & Energy Drinks", "Water"],
#         "Frozen Food": ["Frozen Snacks", "Frozen Vegetables", "Frozen Meat & Fish"],
#         "Dairy & Eggs": ["Milk", "Cheese & Butter", "Eggs", "Yogurt"],
#     },
#     "Baby Food & Care": {
#         "Baby Food": ["Milk Powder", "Cereals & Porridge", "Baby Snacks"],
#         "Baby Care": ["Baby Skin Care", "Baby Bath & Shampoo", "Feeding Bottles"],
#     },

#     "Home Cleaning": {
#         "Laundry": ["Detergent Powder", "Detergent Liquid", "Fabric Softener"],
#         "Dishwashing": ["Dish Soap", "Dish Bar", "Dishwasher Gel"],
#         "Cleaners": ["Floor Cleaner", "Toilet Cleaner", "Glass Cleaner"],
#         "Tissue & Paper": ["Toilet Tissue", "Kitchen Towel", "Facial Tissue"],
#     },
#     "Pet Care": {
#         "Pet Food": ["Dog Food", "Cat Food", "Bird Food"],
#         "Pet Accessories": ["Leash & Collar", "Pet Toys", "Pet Grooming"],
#     },
#     "Beauty & Health": {
#         "Skin Care": ["Face Wash", "Moisturizer & Cream", "Sunscreen", "Face Mask"],
#         "Hair Care": ["Shampoo", "Hair Oil", "Conditioner", "Hair Color"],
#         "Personal Care": ["Soap & Body Wash", "Deodorant", "Oral Care"],
#         "Health Care": ["Vitamins & Supplements", "First Aid", "Medical Devices"],
#     },
#     "Fashion & Lifestyle": {
#         "Men's Fashion": ["T-Shirts", "Panjabi", "Shirts", "Trousers"],
#         "Women's Fashion": ["Saree", "Kurti", "Three Piece", "Abaya"],
#         "Kids Fashion": ["Boys Wear", "Girls Wear", "Baby Wear"],
#         "Footwear": ["Men's Shoes", "Women's Shoes", "Kids Shoes"],
#     },
#     "Home & Kitchen": {
#         "Kitchen Appliances": ["Blender & Mixer", "Rice Cooker", "Induction Cooker"],
#         "Kitchenware": ["Cookware", "Storage & Containers", "Cutlery"],
#         "Home Decor": ["Curtains", "Bedsheets", "Wall Decor"],
#     },
#     "Stationeries": {
#         "School Supplies": ["Notebooks", "Pens & Pencils", "Geometry Box"],
#         "Office Supplies": ["Files & Folders", "Printing Paper", "Staplers & Clips"],
#         "Art Supplies": ["Colors & Crayons", "Drawing Books"],
#     },
#     "Toys & Sports": {
#         "Toys": ["Educational Toys", "Outdoor Toys", "Remote Control Toys", "Soft Toys"],
#         "Sports": ["Cricket", "Football", "Badminton", "Fitness Equipment"],
#     },
#     "Gadget": {
#         "Mobile Accessories": ["Chargers & Cables", "Phone Cases", "Screen Protectors"],
#         "Electronics": ["Power Bank", "Earphones & Headphones", "Bluetooth Speaker"],
#         "Computer Accessories": ["Mouse & Keyboard", "Pen Drive", "Memory Card"],
#     },
# }


CATEGORY_DATA = {
    "Pure Groceries": {
        "Rice": [
            "Premium Miniket Rice",
            "Basmati Rice",
            "Chinigura Rice",
            "Brown Rice",
        ],
        "Lentils & Pulses": [
            "Red Lentils",
            "Mung Dal",
            "Masoor Dal",
            "Chickpeas",
            "Black Gram",
        ],
        "Flour & Atta": [
            "Wheat Atta",
            "Whole Wheat Flour",
            "Rice Flour",
            "Corn Flour",
        ],
        "Edible Oils & Ghee": [
            "Mustard Oil",
            "Olive Oil",
            "Sunflower Oil",
            "Soybean Oil",
            "Organic Ghee",
        ],
        "Salt & Sugar": [
            "Himalayan Pink Salt",
            "Sea Salt",
            "White Sugar",
            "Brown Sugar",
            "Natural Jaggery",
        ],
    },

    "Organic & Healthy Foods": {
        "Organic Foods": [
            "Organic Rice",
            "Organic Lentils",
            "Organic Honey",
            "Organic Ghee",
        ],
        "Sugar-Free Foods": [
            "Sugar-Free Biscuits",
            "Sugar-Free Sweetener",
            "Sugar-Free Jam",
        ],
        "Gluten-Free Foods": [
            "Gluten-Free Flour",
            "Gluten-Free Oats",
            "Gluten-Free Pasta",
        ],
        "Keto Foods": [
            "Almond Flour",
            "Coconut Flour",
            "Keto Snacks",
            "MCT Oil",
        ],
        "Vegan Foods": [
            "Plant-Based Milk",
            "Vegan Protein",
            "Vegan Snacks",
        ],
    },

    "Honey & Natural Sweeteners": {
        "Raw Honey": [
            "Raw Honey",
            "Organic Raw Honey",
        ],
        "Sundarbans Honey": [
            "Pure Sundarbans Honey",
        ],
        "Date Syrup": [
            "Premium Date Syrup",
        ],
        "Maple Syrup": [
            "Pure Maple Syrup",
        ],
        "Natural Jaggery": [
            "Date Palm Jaggery",
            "Sugarcane Jaggery",
        ],
    },

    "Spices & Cooking Essentials": {
        "Whole Spices": [
            "Cinnamon",
            "Cardamom",
            "Cloves",
            "Black Pepper",
        ],
        "Powder Spices": [
            "Turmeric Powder",
            "Chili Powder",
            "Coriander Powder",
            "Cumin Powder",
        ],
        "Mixed Masala": [
            "Garam Masala",
            "Biryani Masala",
            "BBQ Masala",
        ],
        "Herbs & Seasonings": [
            "Oregano",
            "Basil",
            "Mixed Herbs",
        ],
        "Sauces & Vinegar": [
            "Apple Cider Vinegar",
            "Soy Sauce",
            "Tomato Ketchup",
            "Hot Sauce",
        ],
    },

    "Dry Fruits, Nuts & Seeds": {
        "Almonds": [
            "Raw Almonds",
            "Roasted Almonds",
        ],
        "Cashews": [
            "Premium Cashews",
            "Roasted Cashews",
        ],
        "Walnuts": [
            "Walnut Kernels",
        ],
        "Mixed Nuts": [
            "Healthy Mixed Nuts",
        ],
        "Seeds": [
            "Chia Seeds",
            "Flax Seeds",
            "Pumpkin Seeds",
            "Sunflower Seeds",
        ],
    },

    "Baby & Mother Care": {
        "Baby Food": [
            "Baby Formula",
            "Baby Cereal",
            "Baby Puree",
        ],
        "Baby Diapers": [
            "Newborn Diapers",
            "Pant Diapers",
        ],
        "Baby Skin Care": [
            "Baby Lotion",
            "Baby Powder",
            "Baby Shampoo",
        ],
        "Feeding Accessories": [
            "Feeding Bottle",
            "Sipper Cup",
            "Baby Spoon",
        ],
        "Maternity Care": [
            "Stretch Mark Cream",
            "Nursing Pads",
            "Maternity Supplements",
        ],
    },

    "Vitamins & Food Supplements": {
        "Multivitamins": [
            "Adult Multivitamins",
            "Kids Multivitamins",
        ],
        "Calcium & Vitamin D": [
            "Calcium Tablets",
            "Vitamin D3",
        ],
        "Omega-3": [
            "Fish Oil",
            "Omega-3 Capsules",
        ],
        "Protein & Nutrition": [
            "Whey Protein",
            "Collagen Powder",
            "Meal Replacement",
        ],
        "Herbal Supplements": [
            "Ashwagandha",
            "Spirulina",
            "Moringa",
        ],
    },

    "Personal Care & Cosmetics": {
        "Skin Care": [
            "Face Wash",
            "Moisturizer",
            "Sunscreen",
            "Face Serum",
        ],
        "Hair Care": [
            "Shampoo",
            "Conditioner",
            "Hair Oil",
            "Hair Serum",
        ],
        "Oral Care": [
            "Toothpaste",
            "Toothbrush",
            "Mouthwash",
        ],
        "Bath & Body Care": [
            "Soap",
            "Body Wash",
            "Body Lotion",
        ],
        "Natural Cosmetics": [
            "Lip Balm",
            "Natural Face Pack",
            "Essential Oils",
        ],
    },

    "Healthy Beverages": {
        "Green Tea": [
            "Organic Green Tea",
            "Matcha Green Tea",
        ],
        "Herbal Tea": [
            "Chamomile Tea",
            "Tulsi Tea",
            "Ginger Tea",
        ],
        "Coffee": [
            "Instant Coffee",
            "Ground Coffee",
        ],
        "Fresh Juices": [
            "Orange Juice",
            "Mixed Fruit Juice",
        ],
        "Health Drinks": [
            "Oats Drink",
            "Protein Drink",
            "Electrolyte Drink",
        ],
    },

    "Home Health & Wellness": {
        "Medical Devices": [
            "Blood Pressure Monitor",
            "Glucometer",
            "Thermometer",
            "Pulse Oximeter",
        ],
        "First Aid": [
            "Bandage",
            "Antiseptic Solution",
            "First Aid Kit",
        ],
        "Sanitizers & Hygiene": [
            "Hand Sanitizer",
            "Disinfectant Spray",
            "Wet Wipes",
        ],
        "Air Purifiers": [
            "Portable Air Purifier",
            "HEPA Air Purifier",
        ],
        "Aromatherapy": [
            "Essential Oils",
            "Diffuser",
            "Aroma Candles",
        ],
    },
}





class Command(BaseCommand):
    help = "Seed standard category, sub-category and sub-sub-category data"

    def handle(self, *args, **options):
        top_count = sub_count = subsub_count = 0

        for top_name, sub_dict in CATEGORY_DATA.items():
            top_cat, created = Category.objects.get_or_create(
                name=top_name,
                parent=None,
                defaults={
                    "slug": slugify(top_name),
                    "description": f"{top_name} category",
                },
            )
            if created:
                top_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created top category: {top_name}"))
            else:
                self.stdout.write(f"Already exists: {top_name}")

            for sub_name, subsub_list in sub_dict.items():
                sub_cat, created = Category.objects.get_or_create(
                    name=sub_name,
                    parent=top_cat,
                    defaults={
                        "slug": slugify(f"{top_name}-{sub_name}"),
                        "description": f"{sub_name} under {top_name}",
                    },
                )
                if created:
                    sub_count += 1
                    self.stdout.write(f"  Created sub-category: {sub_name}")

                for subsub_name in subsub_list:
                    subsub_cat, created = Category.objects.get_or_create(
                        name=subsub_name,
                        parent=sub_cat,
                        defaults={
                            "slug": slugify(f"{top_name}-{sub_name}-{subsub_name}"),
                            "description": f"{subsub_name} under {sub_name}",
                        },
                    )
                    if created:
                        subsub_count += 1
                        self.stdout.write(f"    Created sub-sub-category: {subsub_name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {top_count} top categories, {sub_count} sub-categories, "
            f"{subsub_count} sub-sub-categories."
        ))
