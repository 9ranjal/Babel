import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { 
  Building2, 
  DollarSign, 
  Users, 
  Shield, 
  Lock, 
  Clock, 
  FileText,
  Plus,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import ChipItem from './ChipItem';
import { 
  chipCategories, 
  getAllChips, 
  getChipsByCategory, 
  getAvailableCategories,
  termSheetThreshold 
} from './informationArchitecture';

const ChipCollection = ({
  onInformationUpdate,
  onTermSheetReady,
  initialData
}) => {
  const [state, setState] = useState({
    chips: getAllChips(),
    completedCategories: [],
    termSheetData: null,
    canGenerateTermSheet: false,
    suggestions: [],
    currentCategory: 'basic_company',
    ...initialData
  });

  const [selectedCategory, setSelectedCategory] = useState('basic_company');

  // Update parent component when state changes
  useEffect(() => {
    onInformationUpdate(state);
  }, [state, onInformationUpdate]);

  // Check if term sheet can be generated
  useEffect(() => {
    const canGenerate = checkTermSheetThreshold();
    setState(prev => ({ ...prev, canGenerateTermSheet: canGenerate }));
    
    if (canGenerate && !state.termSheetData) {
      generateTermSheet();
    }
  }, [state.chips, state.completedCategories]);

  const checkTermSheetThreshold = () => {
    const { requiredCategories, minimumChips, criticalChips } = termSheetThreshold;
    
    // Check if required categories are completed
    const hasRequiredCategories = requiredCategories.every(cat => 
      state.completedCategories.includes(cat)
    );
    
    // Check minimum chips completed
    const completedChips = state.chips.filter(chip => chip.value && chip.value !== '');
    const hasMinimumChips = completedChips.length >= minimumChips;
    
    // Check critical chips
    const hasCriticalChips = criticalChips.every(chipId => {
      const chip = state.chips.find(c => c.id === chipId);
      return chip && chip.value && chip.value !== '';
    });
    
    return hasRequiredCategories && hasMinimumChips && hasCriticalChips;
  };

  const generateTermSheet = () => {
    const completedChips = state.chips.filter(chip => chip.value && chip.value !== '');
    const termSheetData = {
      company: {},
      investors: {},
      deal: {},
      terms: {}
    };

    // Organize data by category
    completedChips.forEach(chip => {
      switch (chip.category) {
        case 'basic_company':
          termSheetData.company[chip.id] = chip.value;
          break;
        case 'securities':
          termSheetData.deal[chip.id] = chip.value;
          break;
        case 'investors':
          termSheetData.investors[chip.id] = chip.value;
          break;
        case 'liquidation_preference':
        case 'anti_dilution':
        case 'vesting':
        case 'registration_rights':
          termSheetData.terms[chip.id] = chip.value;
          break;
      }
    });

    setState(prev => ({ ...prev, termSheetData }));
    onTermSheetReady(termSheetData);
  };

  const handleChipUpdate = (chipId, value) => {
    setState(prev => {
      const updatedChips = prev.chips.map(chip => 
        chip.id === chipId 
          ? { ...chip, value, status: value ? 'completed' : 'pending' }
          : chip
      );

      // Update completed categories
      const updatedCompletedCategories = [...prev.completedCategories];
      const chip = updatedChips.find(c => c.id === chipId);
      
      if (chip && value && !updatedCompletedCategories.includes(chip.category)) {
        updatedCompletedCategories.push(chip.category);
      }

      return {
        ...prev,
        chips: updatedChips,
        completedCategories: updatedCompletedCategories
      };
    });
  };

  const handleChipRemove = (chipId) => {
    setState(prev => ({
      ...prev,
      chips: prev.chips.filter(chip => chip.id !== chipId)
    }));
  };

  const getCategoryIcon = (categoryId) => {
    const icons = {
      basic_company: Building2,
      securities: DollarSign,
      investors: Users,
      liquidation_preference: Shield,
      anti_dilution: Lock,
      vesting: Clock,
      registration_rights: FileText
    };
    return icons[categoryId] || FileText;
  };

  const getCategoryColor = (categoryId) => {
    const colors = {
      basic_company: 'blue',
      securities: 'green',
      investors: 'purple',
      liquidation_preference: 'red',
      anti_dilution: 'orange',
      vesting: 'indigo',
      registration_rights: 'teal'
    };
    return colors[categoryId] || 'gray';
  };

  const getAvailableCategoriesForSelection = () => {
    return getAvailableCategories(state.completedCategories);
  };

  const getChipsForCategory = (categoryId) => {
    return state.chips.filter(chip => chip.category === categoryId);
  };

  const getCategoryProgress = (categoryId) => {
    const categoryChips = getChipsForCategory(categoryId);
    const completedChips = categoryChips.filter(chip => chip.value && chip.value !== '');
    return categoryChips.length > 0 ? (completedChips.length / categoryChips.length) * 100 : 0;
  };

  const getOverallProgress = () => {
    const allChips = state.chips;
    const completedChips = allChips.filter(chip => chip.value && chip.value !== '');
    return allChips.length > 0 ? (completedChips.length / allChips.length) * 100 : 0;
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Term Sheet Information</h2>
            <p className="text-gray-600">Collect information using interactive chips</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-gray-600">Overall Progress</div>
              <div className="text-lg font-semibold">{Math.round(getOverallProgress())}%</div>
            </div>
            <div className="w-32">
              <Progress value={getOverallProgress()} className="h-2" />
            </div>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2">
          {getAvailableCategoriesForSelection().map((category) => {
            const Icon = getCategoryIcon(category.id);
            const progress = getCategoryProgress(category.id);
            const isCompleted = state.completedCategories.includes(category.id);
            
            return (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category.id)}
                className="flex items-center gap-2"
              >
                <Icon className="w-4 h-4" />
                {category.name}
                {isCompleted && <CheckCircle className="w-4 h-4 text-green-600" />}
                <Badge variant="secondary" className="ml-1">
                  {Math.round(progress)}%
                </Badge>
              </Button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          {/* Selected Category Info */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              {React.createElement(getCategoryIcon(selectedCategory), { className: "w-5 h-5" })}
              <h3 className="text-lg font-semibold">
                {chipCategories.find(c => c.id === selectedCategory)?.name}
              </h3>
              <Badge variant="outline" className={`text-${getCategoryColor(selectedCategory)}-600`}>
                {Math.round(getCategoryProgress(selectedCategory))}% Complete
              </Badge>
            </div>
            <p className="text-gray-600 text-sm">
              {chipCategories.find(c => c.id === selectedCategory)?.description}
            </p>
            <div className="mt-2">
              <Progress value={getCategoryProgress(selectedCategory)} className="h-1" />
            </div>
          </div>

          {/* Chips Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {getChipsForCategory(selectedCategory).map((chip) => (
              <ChipItem
                key={chip.id}
                chip={chip}
                onUpdate={handleChipUpdate}
                onRemove={handleChipRemove}
                isEditable={true}
              />
            ))}
          </div>

          {/* Term Sheet Status */}
          {state.canGenerateTermSheet && (
            <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <h4 className="font-semibold text-green-800">Term Sheet Ready!</h4>
              </div>
              <p className="text-green-700 text-sm">
                You have enough information to generate a term sheet. 
                The system will automatically create it based on your inputs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChipCollection;
