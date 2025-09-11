# School Upgrade Analysis System

## 🎯 Overview
A comprehensive web-based system for analyzing school upgrade requirements based on proximity, enrollment, and infrastructure data. The system helps education planners identify schools that need to be upgraded from Primary to Middle, Middle to Secondary, Secondary to High, and High to Higher Secondary levels.

## 🚀 Features

### 📊 Data Management
- **CSV File Upload**: Supports the latest school data format with 23 required columns
- **Real-time Validation**: Instant validation of file format and required columns
- **Drag & Drop Interface**: Easy file upload with visual feedback

### 🎛️ Configurable Analysis
- **Flexible Search Radius**: Adjustable from 5km to 50km with preset options
- **Smart Preset Values**: 
  - 7km (Very Local - Urban areas)
  - 10km (Local - Suburban areas)
  - 15km (Regional - Rural areas)
  - 25km (Standard - Most areas)
  - 30km+ (Wide/District level)

### 🗺️ Interactive Visualization
- **Comprehensive Map View**: Shows ALL schools and upgrade recommendations
- **Color-coded Markers**: Different colors for each school level
- **Upgrade Indicators**: Special markers for schools recommended for upgrade
- **Detailed Popups**: Complete school information and upgrade reasoning

### 📈 Intelligent Algorithm
- **Proximity Analysis**: Identifies areas lacking higher-level schools
- **Enrollment Prioritization**: Selects highest enrollment schools in underserved areas
- **Multi-level Processing**: Handles all upgrade paths simultaneously
- **Comprehensive Reasoning**: Detailed explanations for each recommendation

### 📥 Export & Reporting
- **CSV Download**: Complete recommendations with detailed reasoning
- **Statistical Summary**: Upgrade breakdowns and district analysis
- **Print-friendly Reports**: Clean layouts for documentation

## 📋 Required CSV Columns

Your CSV file must contain exactly these columns:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `BemisCode` | Unique school identifier | 1001 |
| `SchoolName` | Name of the school | "GBPS SAMPLE VILLAGE" |
| `District` | District name | "QUETTA" |
| `Tehsil` | Tehsil name | "QUETTA" |
| `SubTehsil` | Sub-tehsil name | "CENTRAL" |
| `UC` | Union Council | "UC-1" |
| `VillageName` | Village/area name | "Sample Village" |
| `Gender` | Boys/Girls/Mixed | "Boys" |
| `SchoolLevel` | Current education level | "Primary" |
| `FunctionalStatus` | Functional/Non-Functional | "Functional" |
| `ReasonOfNonFunctional` | If non-functional, reason | "" |
| `Building` | Building ownership | "Government" |
| `BuildingStructure` | Construction material | "Concrete" |
| `BuildingCondition` | Condition assessment | "Good" |
| `SpaceForNewRooms` | Expansion possibility | "Yes" |
| `BoundaryWall` | Wall status | "Complete" |
| `BoundaryWallStructure` | Wall material | "Concrete" |
| `BoundaryWallCondition` | Wall condition | "Good" |
| `ElectricityInSchool` | Power availability | "Available" |
| `TotalStudentProfileEntered` | Student count | 125 |
| `Source` | Data source | "EMIS" |
| `_xCord` | Longitude coordinate | 67.0101 |
| `_yCord` | Latitude coordinate | 30.1801 |

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation Steps

1. **Navigate to the system directory:**
   ```bash
   cd /Users/macbookpro/Desktop/PMC/SchoolUpgradeSystem
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the system:**
   Open your browser and go to: `http://127.0.0.1:5002`

## 📖 Usage Guide

### Step 1: Upload Data
1. Go to the main page
2. Click "Choose File" or drag & drop your CSV file
3. System validates file format automatically
4. If valid, proceed to configuration

### Step 2: Configure Analysis
1. Set search radius using slider or preset buttons
2. Optionally set minimum enrollment filter
3. Optionally filter by specific district
4. Click "Start Analysis"

### Step 3: Review Results
1. View interactive map showing all schools
2. Review statistical summary
3. Examine detailed table of recommendations
4. Download CSV file with complete results

## 🎯 Algorithm Logic

### Upgrade Criteria
1. **No Higher-Level School**: Must have no higher-level school within search radius
2. **Enrollment Priority**: Among multiple same-level schools, prioritize highest enrollment
3. **Functional Status**: Only considers functional schools
4. **Geographic Scope**: Analysis performed district-wise for efficiency

### Upgrade Paths
- **Primary → Middle**
- **Middle → Secondary**
- **Secondary → High**
- **High → Higher Secondary**

### Search Strategy
- **District-based Processing**: Analyzes each district separately
- **Level-by-level Analysis**: Processes each upgrade type systematically
- **Distance Calculation**: Uses geodesic distance for accuracy
- **Enrollment Ranking**: Selects top 80th percentile by enrollment

## 📊 Output Files

### CSV Download Contents
- All input columns preserved
- Additional analysis columns:
  - `CurrentLevel`: Original school level
  - `RecommendedLevel`: Suggested upgrade level
  - `UpgradeReason`: Detailed explanation
  - `SearchRadius_km`: Radius used in analysis
  - `AnalysisDate`: Timestamp of analysis
  - `NearbyHigherSchools`: Count of higher-level schools nearby
  - `NearbySameLevelSchools`: Count of same-level schools nearby

## 🗂️ File Structure

```
SchoolUpgradeSystem/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── sample_data.csv       # Sample data file
├── templates/            # HTML templates
│   ├── index.html        # Upload page
│   ├── configure.html    # Configuration page
│   └── results.html      # Results display
├── uploads/              # Uploaded files storage
└── downloads/            # Generated reports storage
```

## 🔧 Customization Options

### Radius Presets
You can modify the preset radius values in `configure.html`:
```javascript
const radiusDescriptions = {
    5: "Very strict local analysis...",
    // Add your custom descriptions
};
```

### School Level Hierarchy
Modify upgrade paths in `app.py`:
```python
UPGRADE_MAPPING = {
    'Primary': 'Middle',
    'Middle': 'Secondary',
    # Add custom upgrade paths
}
```

### Map Styling
Customize map colors and markers in the `create_upgrade_map()` function.

## 🚨 Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file has all required columns
   - Ensure coordinate data is numeric
   - Verify CSV format is valid

2. **No Results Found**
   - Try smaller search radius
   - Check if schools have valid coordinates
   - Verify functional status in data

3. **Map Not Loading**
   - Check internet connection for map tiles
   - Ensure coordinate data is within valid ranges
   - Verify browser JavaScript is enabled

### Error Messages
- **"Missing required columns"**: Your CSV is missing mandatory fields
- **"No functional schools found"**: All schools are marked non-functional
- **"Analysis failed"**: Check coordinate data quality

## 📞 Support & Maintenance

### Regular Updates
- Update school data quarterly
- Review radius settings annually
- Validate coordinate accuracy

### Performance Tips
- Use enrollment filters for large datasets
- Process districts separately for very large files
- Regular cleanup of upload/download folders

## 🔐 Security Considerations

- File size limited to 50MB
- Only CSV files accepted
- Temporary file cleanup after processing
- No sensitive data persistence

## 📝 Version History

- **v2.0** (July 2025): Complete web interface with interactive maps
- **v1.0** (July 2025): Basic command-line analysis tool

---

**Last Updated**: July 29, 2025  
**Version**: 2.0  
**Compatibility**: Python 3.9+, Modern web browsers
