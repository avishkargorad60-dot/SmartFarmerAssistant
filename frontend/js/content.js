// ---------------------------------------------------------------------------
// Plain-language explanations shown alongside real backend results.
// These do not invent predictions or prices — they only add friendly
// context to labels the backend already returned (soil type, disease name).
// Soil keys mirror agents/crop_recommendation_agnet: CROP_DATA "soils" values.
// Disease keys mirror agents/disease_agent/class_names.json exactly.
// ---------------------------------------------------------------------------

export const SOIL_INFO = {
  "black soil": {
    summary: "Rich in clay and holds moisture well, black soil is prized for cotton, soybean and pigeon pea.",
    implication: "It stays moist for longer, so fields need fewer irrigations but should be watched for waterlogging after heavy rain.",
  },
  "alluvial soil": {
    summary: "A fertile soil formed by river deposits, common across northern and eastern plains.",
    implication: "Naturally fertile and good for a wide range of crops, but benefits from balanced fertiliser use season after season.",
  },
  "red soil": {
    summary: "Iron-rich soil that drains quickly and is common in central and southern regions.",
    implication: "Drains fast, so it needs more frequent watering and does well with organic matter to hold nutrients.",
  },
  "laterite soil": {
    summary: "Formed in high-rainfall areas, laterite soil is porous with lower natural fertility.",
    implication: "Often needs added organic manure and lime, and suits hardy, rain-tolerant crops like cashew and tea.",
  },
  "yellow soil": {
    summary: "A lower-fertility soil related to red soil, found in drier upland areas.",
    implication: "Responds well to organic compost and crops that tolerate modest fertility, like groundnut or millets.",
  },
  "mountain soil": {
    summary: "Found on hill slopes, this soil varies with altitude and is generally rich in organic matter.",
    implication: "Good for tea, wheat and fruit crops, though slopes need care to prevent soil erosion.",
  },
  "arid soil": {
    summary: "A dry-region soil, sandy and low in organic matter, common in low-rainfall belts.",
    implication: "Needs drought-tolerant crops and careful water management; adding organic matter improves it over time.",
  },
};

export function soilInfoFor(soilType) {
  if (!soilType) return null;
  const key = String(soilType).toLowerCase().replace(/_/g, " ").trim();
  return SOIL_INFO[key] || null;
}

// Each entry: friendlyName, crop, condition ("healthy" | disease name), status.
export const DISEASE_INFO = {
  "Pepper__bell___Bacterial_spot": {
    crop: "Bell Pepper", friendly: "Bacterial Spot", healthy: false,
    summary: "A bacterial infection that causes dark, water-soaked spots on leaves and fruit.",
  },
  "Pepper__bell___healthy": {
    crop: "Bell Pepper", friendly: "Healthy", healthy: true,
    summary: "This plant shows no visible signs of disease.",
  },
  "Potato___Early_blight": {
    crop: "Potato", friendly: "Early Blight", healthy: false,
    summary: "A fungal disease that creates dark, ring-patterned spots, usually starting on older leaves.",
  },
  "Potato___Late_blight": {
    crop: "Potato", friendly: "Late Blight", healthy: false,
    summary: "A fast-spreading fungal disease that causes dark, blotchy patches, especially in cool, wet weather.",
  },
  "Potato___healthy": {
    crop: "Potato", friendly: "Healthy", healthy: true,
    summary: "This plant shows no visible signs of disease.",
  },
  "Tomato_Bacterial_spot": {
    crop: "Tomato", friendly: "Bacterial Spot", healthy: false,
    summary: "Small, dark, greasy-looking spots on leaves and fruit caused by bacteria.",
  },
  "Tomato_Early_blight": {
    crop: "Tomato", friendly: "Early Blight", healthy: false,
    summary: "A fungal disease showing target-like rings on older leaves first.",
  },
  "Tomato_Late_blight": {
    crop: "Tomato", friendly: "Late Blight", healthy: false,
    summary: "A serious fungal disease that spreads quickly in cool, damp conditions.",
  },
  "Tomato_Leaf_Mold": {
    crop: "Tomato", friendly: "Leaf Mold", healthy: false,
    summary: "A fungal disease common in humid conditions, showing pale patches with fuzzy mold underneath leaves.",
  },
  "Tomato_Septoria_leaf_spot": {
    crop: "Tomato", friendly: "Septoria Leaf Spot", healthy: false,
    summary: "Numerous small circular spots with dark edges, usually starting on lower leaves.",
  },
  "Tomato_Spider_mites_Two_spotted_spider_mite": {
    crop: "Tomato", friendly: "Spider Mite Damage", healthy: false,
    summary: "Tiny pests that cause speckled, discoloured leaves and fine webbing, especially in hot, dry weather.",
  },
  "Tomato__Target_Spot": {
    crop: "Tomato", friendly: "Target Spot", healthy: false,
    summary: "A fungal disease that produces concentric ring spots similar to a target.",
  },
  "Tomato__Tomato_YellowLeaf__Curl_Virus": {
    crop: "Tomato", friendly: "Yellow Leaf Curl Virus", healthy: false,
    summary: "A viral disease, usually spread by whiteflies, that causes yellowing and upward curling of leaves.",
  },
  "Tomato__Tomato_mosaic_virus": {
    crop: "Tomato", friendly: "Mosaic Virus", healthy: false,
    summary: "A viral disease causing a mottled, mosaic-like pattern of light and dark green on leaves.",
  },
  "Tomato_healthy": {
    crop: "Tomato", friendly: "Healthy", healthy: true,
    summary: "This plant shows no visible signs of disease.",
  },
};

export function diseaseInfoFor(label) {
  if (!label) return null;
  if (DISEASE_INFO[label]) return DISEASE_INFO[label];
  // Fall back gracefully if the backend model/class list ever changes.
  const healthy = /healthy/i.test(label);
  return {
    crop: null,
    friendly: label.replace(/_+/g, " ").replace(/\s+/g, " ").trim(),
    healthy,
    summary: healthy
      ? "This plant shows no visible signs of disease."
      : "The photo shows signs that may need attention.",
  };
}

export const FARMING_TIPS = [
  "Rotate crops each season to keep soil nutrients balanced and reduce pest build-up.",
  "Water early in the morning to reduce evaporation loss and fungal disease risk.",
  "Test your soil every couple of seasons — it's the most reliable way to plan fertiliser use.",
  "Mulching around plants helps retain soil moisture and suppress weeds.",
  "Inspect crops weekly for early signs of pests or disease — early action is easier and cheaper.",
  "Mixing crop varieties or intercropping can reduce the risk of losing an entire field to one problem.",
  "Keep field edges clean; many pests and diseases spread from untended borders.",
  "Store harvested grain in a dry, well-ventilated place to avoid spoilage.",
];

export function tipOfTheDay() {
  const dayIndex = Math.floor(Date.now() / 86400000);
  return FARMING_TIPS[dayIndex % FARMING_TIPS.length];
}
