import tkinter as tk
from tkinter import messagebox
import sqlite3
import pygame
import requests
from io import BytesIO
import tempfile

# Initialize pygame mixer for music
pygame.mixer.init()

# URL of royalty-free vending machine-style music
music_url = 'https://filesamples.com/samples/audio/mp3/sample2.mp3'

# Function to play music from URL
def play_music_from_url(url):
    try:
        # Download the audio file
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            temp_audio_file.write(response.content)
            temp_audio_path = temp_audio_file.name

        # Load and play the audio
        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.play(-1)  # Loop the music indefinitely

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the music: {e}")
    except pygame.error as e:
        print(f"Error playing the music: {e}")

# Play music from URL
play_music_from_url(music_url)

# Function to load products from database
def load_products_from_db():
    conn = sqlite3.connect('vending_machine.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    
    products = {}
    for row in cursor.fetchall():
        product_id, name, price, category, stock = row
        products[product_id] = {"id": product_id, "name": name, "price": price, "category": category, "stock": stock}
    
    conn.close()
    return products

# Function to update stock in the database
def update_stock_in_db(product_id, new_stock):
    conn = sqlite3.connect('vending_machine.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Products SET stock = ? WHERE id = ?", (new_stock, product_id))
    conn.commit()
    conn.close()

# Function to display products in the GUI
def display_products(products, product_listbox):
    product_listbox.delete(0, tk.END)
    for product_id, product_info in products.items():
        product_listbox.insert(tk.END, f"{product_info['name']} - ${product_info['price']} (Stock: {product_info['stock']})")

# Function to handle purchasing in the GUI
def purchase_item(products, product_listbox, quantity_entry, money_entry, suggestion_listbox):
    selected_index = product_listbox.curselection()
    if not selected_index:
        messagebox.showerror("Error", "Please select a product.")
        return

    # Get the selected product from the list
    selected_product = list(products.values())[selected_index[0]]
    quantity = quantity_entry.get()
    money_inserted = money_entry.get()

    try:
        quantity = int(quantity)
        money_inserted = float(money_inserted)

        # Ensure the quantity is within stock limits
        if quantity > selected_product['stock']:
            messagebox.showerror("Error", f"Only {selected_product['stock']} items are available in stock.")
        else:
            total_price = quantity * selected_product['price']
            if money_inserted >= total_price:
                change = money_inserted - total_price
                selected_product['stock'] -= quantity
                update_stock_in_db(selected_product['id'], selected_product['stock'])
                messagebox.showinfo("Success", f"{quantity} {selected_product['name']} dispensed.\nYour change: ${change:.2f}")
                display_products(products, product_listbox)

                # Suggest products from the same category
                suggest_products(products, selected_product['category'], suggestion_listbox)
            else:
                messagebox.showerror("Error", "Not enough money inserted.")
    except ValueError:
        messagebox.showerror("Error", "Invalid quantity or money entered.")

# Function to suggest products based on category
def suggest_products(products, category, suggestion_listbox):
    # Clear the existing suggestions
    suggestion_listbox.delete(0, tk.END)

    # Find products with the same category
    suggestions = [product for product in products.values() if product['category'] == category]
    
    if suggestions:
        for product in suggestions:
            suggestion_listbox.insert(tk.END, f"{product['name']} - ${product['price']} (Stock: {product['stock']})")
    else:
        suggestion_listbox.insert(tk.END, "No suggestions available.")

# GUI Setup
def setup_gui():
    root = tk.Tk()
    root.title("Mars Vending Machine")

    # Set the background color and style to match a Mars theme
    root.configure(bg='#2C2C2C')  # Dark grey background (space-like)

    # Load products from DB
    products = load_products_from_db()

    # Create GUI components
    product_listbox = tk.Listbox(root, width=50, height=10, bg='#D9534F', fg='white', font=("Helvetica", 12))
    display_products(products, product_listbox)
    product_listbox.grid(row=0, column=0, padx=10, pady=10)

    quantity_label = tk.Label(root, text="Quantity:", fg='white', bg='#2C2C2C', font=("Helvetica", 12))
    quantity_label.grid(row=1, column=0, padx=10, pady=10)
    quantity_entry = tk.Entry(root, font=("Helvetica", 12))
    quantity_entry.grid(row=1, column=1, padx=10, pady=10)

    money_label = tk.Label(root, text="Money Inserted:", fg='white', bg='#2C2C2C', font=("Helvetica", 12))
    money_label.grid(row=2, column=0, padx=10, pady=10)
    money_entry = tk.Entry(root, font=("Helvetica", 12))
    money_entry.grid(row=2, column=1, padx=10, pady=10)

    purchase_button = tk.Button(root, text="Purchase", bg='#F1C40F', fg='black', font=("Helvetica", 14), command=lambda: purchase_item(products, product_listbox, quantity_entry, money_entry, suggestion_listbox))
    purchase_button.grid(row=3, column=0, columnspan=2, pady=10)

    exit_button = tk.Button(root, text="Exit", bg='#E74C3C', fg='white', font=("Helvetica", 14), command=root.quit)
    exit_button.grid(row=4, column=0, columnspan=2, pady=10)

    # Suggestion Listbox (to show related products)
    suggestion_label = tk.Label(root, text="Suggested Products:", fg='white', bg='#2C2C2C', font=("Helvetica", 12))
    suggestion_label.grid(row=0, column=2, padx=10, pady=10)
    suggestion_listbox = tk.Listbox(root, width=40, height=10, bg='#E67E22', fg='white', font=("Helvetica", 12))
    suggestion_listbox.grid(row=1, column=2, rowspan=3, padx=10, pady=10)

    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    setup_gui()
