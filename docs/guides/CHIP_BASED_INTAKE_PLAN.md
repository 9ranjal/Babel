# Chip-Based Information Collection System Plan

## 🎯 **Overview**
Replace both structured forms and conversational intake with a **dynamic chip system** for term sheet information collection.

## 📋 **Core Concept**
- Users collect information through **contextual chips**
- Each chip represents a **specific data point** or **category**
- **Progressive disclosure** - chips appear based on previous selections
- **Real-time term sheet generation** once threshold is met
- **Dynamic updates** as users add/modify information

## 🏗️ **Information Architecture**

### **A. Basic Company Information**
- Company Name
- Jurisdiction (State/Country)
- Business Description
- Industry Classification

### **B. Securities & Offering**
- Security Type (Preferred Stock, Common Stock, etc.)
- Number of Shares
- Price per Share
- Total Offering Size
- Pre-money Valuation

### **C. Investor Information**
- Lead Investor
- Investor Type (VC, PE, Angel, etc.)
- Investment Amount
- Ownership Percentage
- Board Seats

### **D. Key Terms Categories**
- **Liquidation Preference** (1x, 2x, participating/non-participating)
- **Anti-dilution Protection** (Weighted average, Full ratchet)
- **Voting Rights** (Board seats, protective provisions)
- **Registration Rights** (Demand, piggyback, S-3)
- **Vesting** (Founder vesting, employee vesting)
- **Drag-along/Tag-along Rights**
- **Right of First Refusal**
- **Management Rights**

## 🔧 **Technical Implementation**

### **Chip Types & States**
```typescript
interface ChipData {
  id: string;
  category: string;
  label: string;
  value: any;
  status: 'pending' | 'completed' | 'required' | 'optional';
  dependencies?: string[];
  options?: string[];
  type: 'text' | 'select' | 'number' | 'boolean' | 'date';
}
```

### **State Management**
```typescript
interface InformationState {
  chips: ChipData[];
  completedCategories: string[];
  termSheetData: any;
  canGenerateTermSheet: boolean;
  suggestions: ChipData[];
}
```

## 🚀 **Implementation Phases**

### **Phase 1: Core Chip System** ✅
- Basic chip components
- Simple information collection
- Static chip generation
- Basic term sheet template

### **Phase 2: AI Integration**
- Ollama integration for chip suggestions
- Context-aware chip generation
- Smart defaults based on selections
- Dynamic term sheet updates

### **Phase 3: Advanced Features**
- Real-time collaboration
- Version control
- Export capabilities
- Integration with external systems

## 🎨 **User Experience Flow**

### **Phase 1: Initial Information Collection**
1. User sees basic company info chips
2. Fills in company name, jurisdiction
3. System suggests industry-specific chips
4. User adds investor information
5. System generates deal structure chips

### **Phase 2: Term Sheet Generation**
1. Threshold reached (basic company + investor + key terms)
2. System generates initial term sheet
3. User can add more specific terms via chips
4. Term sheet updates in real-time
5. User can refine any section

### **Phase 3: Refinement & Completion**
1. User reviews generated term sheet
2. Adds missing information via chips
3. Modifies existing terms
4. System suggests additional clauses
5. Final term sheet generation

## 🎯 **Key Benefits**
1. **Intuitive Interface** - Visual, interactive information collection
2. **Contextual Guidance** - AI suggests relevant information
3. **Progressive Disclosure** - Only show relevant chips
4. **Real-time Updates** - Term sheet updates as you go
5. **Flexible Workflow** - Users can jump between sections
6. **Smart Defaults** - Reduces manual input
7. **Comprehensive Coverage** - Based on industry-standard questionnaires

## 📁 **File Structure**
```
frontend-cra-old/src/components/chips/
├── ChipCollection.tsx          # Main container
├── ChipItem.tsx               # Individual chip component
├── ChipGenerator.tsx          # AI-powered chip suggestions
├── ChipCategories.tsx         # Category management
└── hooks/
    ├── useChipState.ts        # Chip state management
    ├── useChipSuggestions.ts  # AI suggestions
    └── useTermSheetGeneration.ts # Term sheet logic
```
