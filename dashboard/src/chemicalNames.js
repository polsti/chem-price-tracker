// Ukrainian display names, keyed by chemical_id (stable — matches the
// site's own IDs). The English chemical_name from the database/scraper
// is never changed, only what's shown on screen here.
const UKRAINIAN_NAMES = {
  "449": "Ацетон",
  "678": "Жовтий фосфор",
  "1658": "Жирні спирти",
  "114793214": "Моноетаноламін",
  "499": "Оцтова кислота",
  "366": "Метанол",
  "377": "Чистий бензол",
  "367": "Етиленгліколь",
};

// Falls back to the English name if a chemical_id isn't in the list above
// (e.g. a new chemical gets added before someone remembers to translate it).
export function displayName(chem) {
  return UKRAINIAN_NAMES[chem.chemical_id] || chem.chemical_name;
}
