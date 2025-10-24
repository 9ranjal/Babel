# Chip-Based Information Collection System

A modern, interactive approach to collecting term sheet information using contextual chips instead of traditional forms or conversational interfaces.

## 🎯 **Overview**

This system replaces both the structured form (`TermSheetInfoCollector.jsx`) and conversational intake (`PersonaIntake.tsx`) with a dynamic chip-based interface that:

- **Progressive Disclosure**: Shows relevant chips based on previous selections
- **Contextual Guidance**: AI-powered suggestions for industry-specific terms
- **Real-time Updates**: Term sheet generates automatically when threshold is met
- **Flexible Workflow**: Users can jump between categories and edit any information

## 🏗️ **Architecture**

### **Core Components**

- **`ChipCollection.tsx`** - Main container component
- **`ChipItem.tsx`** - Individual chip component with editing capabilities
- **`ChipSystemDemo.tsx`** - Demo page showcasing the system

### **Hooks**

- **`useChipState.ts`** - State management for chips and categories
- **`useChipSuggestions.ts`** - AI-powered suggestion generation

### **Information Architecture**

- **`informationArchitecture.ts`** - Defines all chip categories and data structures
- **`types.ts`** - TypeScript definitions for the system

## 📋 **Information Categories**

### **1. Basic Company Information**
- Company Name
- Jurisdiction
- Business Description
- Industry Classification

### **2. Securities & Offering**
- Security Type
- Number of Shares
- Price per Share
- Total Offering Size
- Pre-money Valuation

### **3. Investor Information**
- Lead Investor
- Investor Type
- Investment Amount
- Ownership Percentage
- Board Seats

### **4. Key Terms**
- **Liquidation Preference** - Multiple, participating status
- **Anti-dilution Protection** - Weighted average, full ratchet
- **Vesting** - Founder and employee vesting schedules
- **Registration Rights** - Demand, piggyback, S-3 rights

## 🚀 **Usage**

### **Basic Implementation**

```tsx
import { ChipCollection } from './components/chips';

function MyComponent() {
  const handleInformationUpdate = (state: InformationState) => {
    console.log('Information updated:', state);
  };

  const handleTermSheetReady = (data: any) => {
    console.log('Term sheet ready:', data);
  };

  return (
    <ChipCollection
      onInformationUpdate={handleInformationUpdate}
      onTermSheetReady={handleTermSheetReady}
    />
  );
}
```

### **With Custom State**

```tsx
import { useChipState } from './components/chips';

function CustomChipComponent() {
  const {
    state,
    updateChip,
    getChipsByCategory,
    getOverallProgress
  } = useChipState();

  return (
    <div>
      <div>Progress: {getOverallProgress()}%</div>
      {/* Your custom UI */}
    </div>
  );
}
```

## 🎨 **Key Features**

### **1. Progressive Disclosure**
- Categories unlock based on dependencies
- Only show relevant chips
- Smart defaults based on selections

### **2. Real-time Term Sheet Generation**
- Automatic generation when threshold is met
- Dynamic updates as information changes
- Industry-standard templates

### **3. Contextual Suggestions**
- AI-powered chip suggestions
- Industry-specific terms
- Smart defaults based on company type

### **4. Flexible Editing**
- Edit any chip at any time
- Visual status indicators
- Validation and error handling

## 🔧 **Configuration**

### **Term Sheet Threshold**
```typescript
const termSheetThreshold = {
  requiredCategories: ['basic_company', 'securities', 'investors'],
  minimumChips: 8,
  criticalChips: [
    'company_name',
    'jurisdiction',
    'security_type',
    'offering_size',
    'pre_money_valuation',
    'lead_investor',
    'investment_amount',
    'ownership_percentage'
  ]
};
```

### **Adding New Categories**
```typescript
const newCategory: ChipCategory = {
  id: 'custom_terms',
  name: 'Custom Terms',
  description: 'Custom terms for specific needs',
  icon: 'CustomIcon',
  color: 'blue',
  chips: customChips,
  dependencies: ['basic_company'],
  order: 8
};
```

## 🧪 **Testing**

### **Demo Page**
Visit `/chip-based-intake` to see the system in action.

### **Development Mode**
The demo includes debug information showing:
- Completed categories
- Term sheet generation status
- Progress metrics

## 🔄 **Migration from Old Systems**

### **From Structured Forms**
- Replace `TermSheetInfoCollector.jsx` with `ChipCollection.tsx`
- Map form fields to chip categories
- Update data handling logic

### **From Conversational Intake**
- Replace `PersonaIntake.tsx` with chip system
- Convert Q&A flow to chip categories
- Maintain persona creation logic

## 🎯 **Benefits**

1. **Better UX** - Visual, interactive information collection
2. **Contextual Guidance** - AI suggests relevant information
3. **Progressive Disclosure** - Only show what's needed
4. **Real-time Updates** - Term sheet updates as you go
5. **Flexible Workflow** - Jump between sections freely
6. **Smart Defaults** - Reduces manual input
7. **Comprehensive Coverage** - Based on industry standards

## 🔮 **Future Enhancements**

- **AI Integration** - Ollama-powered suggestions
- **Collaboration** - Multi-user editing
- **Version Control** - Track changes over time
- **Export Options** - Multiple output formats
- **Integration** - Connect with external systems
