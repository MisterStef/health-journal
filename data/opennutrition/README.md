# OpenNutrition data used by this app

These files are derived from the OpenNutrition Dataset 2025.1 (https://www.opennutrition.app) and are shared under the Open Database License (ODbL 1.0), the same license as the source. See LICENSE-ODbL.txt and LICENSE-DbCL.txt.

Portions of the OpenNutrition dataset incorporate data from Open Food Facts: (c) Open Food Facts contributors, https://world.openfoodfacts.org

What was changed: nutrition per 100 g was converted to the listed serving size, limited to the nutrients this app tracks, ethyl alcohol was converted to US standard drinks (14 g), and the data was split into foods.json (everyday, prepared and restaurant foods) and barcode files grouped by the first digits of the EAN-13 code. Built by build_on.py in this folder.
