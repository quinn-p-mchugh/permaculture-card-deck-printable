# Learn permaculture principles by printing your own permaculture card deck
<img src="readme-banner.jpg" width="100%" alt="Banner" />

This repository contains a **easy-to-print** version of the **[Permaculture Design Deck](https://www.permaculturedesign.earth/designdeck)** (2022 version), created by Delvin Solkinson, Grace Solkinson, and their collaborators. Print-ready PDFs are provided in both **US Letter (8.5 x 11 in)** and **A4 (210 x 297 mm)** formats.

You can [purchase a professionally printed copy of the card deck on Etsy](https://www.etsy.com/shop/DewPermaculture) or [download it as a free PDF version](https://www.dropbox.com/scl/fi/z9gd4df9oiha6be0gzayf/Permaculture-Design-Deck-2022.pdf?rlkey=ujrdfzl7xmocu05ioaguix1xn&e=1&dl=0) on [permaculturedesign.earth](https://www.permaculturedesign.earth/).

All credit for the creation of this deck belongs to Delvin, Grace, and their collaborators (listed below). Please consider [donating](https://www.paypal.com/donate/?hosted_button_id=MM79QGM4PW2FS) to support their work and help keep the downloads on their website free.

## Why this repository exists
While the freely available PDF is great for viewing, its layout makes it difficult to print at home, especially as a two-sided card deck. This repository reorganizes the cards into a print-ready format so you can print, cut, and assemble your own deck with minimal hassle.

## How to print
1. Download the PDF file in the `card-deck-printable-pdfs` folder that matches your paper size: 
    - For **US Letter (8.5 × 11 in)** paper, download the `letter-size` PDF.
    - For **A4 (210 x 297 mm)** paper, download the `a4-size` PDF.
3. Open the desired PDF and select **Print**.
4. In the print dialog:
    - Enable **Print on both sides of paper**. This setting may be labeled **Two-Sided Printing**, **Duplex Printing**, **Print Double-Sided**, **Print on Both Sides**, etc.
    - Select **Flip on Short Edge**. This setting may be labeled **Short-Edge Binding**, **Bind on Short Edge**, **Short Edge**, **Flip Pages on Short Edge**, etc.
4. Print at **Actual Size** or **100% scale**.
5. Cut each card out along the cut guides and assemble the deck.

## What is the Permaculture Design Deck?
*From [permaculturedesign.earth/designdeck](https://www.permaculturedesign.earth/designdeck):*
> Sharing the Secrets of Natures Success, permaculture is a toolkit for becoming a more effective decision maker
> and designer. Skill up and become better. Take your design life to the next level.  
> 
> Creative card deck sharing a collection of permaculture principles,
> strategies, attitudes, tools & frameworks. 230 cards to support your
> permaculture practice, learning, teaching, designing and consulting.
> Serves as a design tool, game and oracle.
> 
> Awesome gratitude to our core team: Grace Solkinson, Kym Chi, Dana
> Wilson, Annaliese Hordern, Tamara Griffiths
> 
> Special thanks to Jason Gerhardt, Maddy Harland, Wilf Richards, Chris
> Evans and Aranya for ongoing mentorship and support that unlocked this
> deck. Grateful to Tamara Griffiths who helped identify many of the
> principles in early versions of the deck.
> 
> This work is the culmination of 20 years of Permaculture Design study
> by Delvin Solkinson which spanned 13 advanced courses and 13 teacher
> trainings, a PDC, Diploma and Masters Degree with Bill Mollison, a
> second Diploma through the Permaculture Institute, a third Diploma
> through the Permaculture Association with Looby Macnamara, and a
> Doctorate through the Permaculture Academy and Larry Santoyo. This
> newest version is a core project in a Post-Doc in Permaculture
> Education.
> 
> Art by Brenna Quinlan Design by Alexa Spaddy Text Design by Sijay
> James Onbeyond Metamedia
> 
> This deck is a companion for the Permaculture Design Notes and
> Permaculture Design Elements Game. Together they form a toolkit
> sharing a creative essence of Permaculture Design.
> 
> [https://www.etsy.com/shop/DewPermaculture](https://www.etsy.com/your/shops/DewPermaculture/tools/listings)

## Editing Card Layouts 
This repository includes a `cider-database.json` file that can be imported into the [Cider](https://oatear.github.io/cider/), a free, open source card design studio. The database contains the card content and layout data used to generate the printable PDFs in this repository.

To import the database into Cider:

1. Open https://oatear.github.io/cider/
2. Open the **☰ (hamburger menu)** in the top-left corner.
3. Select **File → Advanced → Import Database**.
4. Choose `cider-database.json`.

If you need to modify the print layout, you can import this file into Cider and regenerate the PDFs. This may be useful for adjusting margins, repositioning elements, or making other layout changes for your printer.

After editing, you can export the updated PDFs from Cider for printing.

For more information about using Cider, see the [Cidar project documentation](https://github.com/oatear/cider).

## Regenerating the Cider Database

This repository includes `build_cider_deck.py`, a utility that converts the original Permaculture Design Deck PDF into a Cider-compatible `database.json` file.

### Requirements

* Python 3
* `pdftoppm` (part of the Poppler utilities)
* Optional: `Pillow` (`pip install Pillow`) for image downscaling

### Usage

```bash
python3 build_cider_deck.py
```

Or specify custom paths:

```bash
python3 build_cider_deck.py INPUT_PDF OUTPUT_JSON
```

### What It Does

The script assumes the PDF is organized as alternating front and back pages:

* Page 1 = Card 1 Front
* Page 2 = Card 1 Back
* Page 3 = Card 2 Front
* Page 4 = Card 2 Back
* etc.

It then:

1. Renders each PDF page to an image.
2. Pairs front and back images into cards.
3. Builds a Cider-compatible `database.json`.
4. Saves individual card images for reference.

### Importing into Cider

1. Open https://oatear.github.io/cider/
2. Open the **☰ (hamburger menu)** in the top-left corner.
3. Select **File → Advanced → Import Database**.
4. Choose `cider-database.json`.
