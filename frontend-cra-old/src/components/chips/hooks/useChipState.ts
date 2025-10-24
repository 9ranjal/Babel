import { useState, useEffect, useCallback } from 'react';
import { ChipData, InformationState, ChipCategory } from '../types';
import { getAllChips, getAvailableCategories, termSheetThreshold } from '../informationArchitecture';

export const useChipState = (initialState?: Partial<InformationState>) => {
  const [state, setState] = useState<InformationState>({
    chips: getAllChips(),
    completedCategories: [],
    termSheetData: null,
    canGenerateTermSheet: false,
    suggestions: [],
    currentCategory: 'basic_company',
    ...initialState
  });

  // Update chip value
  const updateChip = useCallback((chipId: string, value: any) => {
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
  }, []);

  // Remove chip
  const removeChip = useCallback((chipId: string) => {
    setState(prev => ({
      ...prev,
      chips: prev.chips.filter(chip => chip.id !== chipId)
    }));
  }, []);

  // Add new chip
  const addChip = useCallback((chip: ChipData) => {
    setState(prev => ({
      ...prev,
      chips: [...prev.chips, chip]
    }));
  }, []);

  // Update multiple chips
  const updateChips = useCallback((updates: Record<string, any>) => {
    setState(prev => {
      const updatedChips = prev.chips.map(chip => 
        updates.hasOwnProperty(chip.id) 
          ? { ...chip, value: updates[chip.id], status: updates[chip.id] ? 'completed' : 'pending' }
          : chip
      );

      // Update completed categories
      const updatedCompletedCategories = [...prev.completedCategories];
      Object.entries(updates).forEach(([chipId, value]) => {
        if (value) {
          const chip = updatedChips.find(c => c.id === chipId);
          if (chip && !updatedCompletedCategories.includes(chip.category)) {
            updatedCompletedCategories.push(chip.category);
          }
        }
      });

      return {
        ...prev,
        chips: updatedChips,
        completedCategories: updatedCompletedCategories
      };
    });
  }, []);

  // Check if term sheet can be generated
  const checkTermSheetThreshold = useCallback(() => {
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
  }, [state.completedCategories, state.chips]);

  // Get chips by category
  const getChipsByCategory = useCallback((categoryId: string) => {
    return state.chips.filter(chip => chip.category === categoryId);
  }, [state.chips]);

  // Get available categories
  const getAvailableCategoriesForSelection = useCallback(() => {
    return getAvailableCategories(state.completedCategories);
  }, [state.completedCategories]);

  // Get category progress
  const getCategoryProgress = useCallback((categoryId: string) => {
    const categoryChips = getChipsByCategory(categoryId);
    const completedChips = categoryChips.filter(chip => chip.value && chip.value !== '');
    return categoryChips.length > 0 ? (completedChips.length / categoryChips.length) * 100 : 0;
  }, [getChipsByCategory]);

  // Get overall progress
  const getOverallProgress = useCallback(() => {
    const allChips = state.chips;
    const completedChips = allChips.filter(chip => chip.value && chip.value !== '');
    return allChips.length > 0 ? (completedChips.length / allChips.length) * 100 : 0;
  }, [state.chips]);

  // Generate term sheet data
  const generateTermSheetData = useCallback(() => {
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

    return termSheetData;
  }, [state.chips]);

  // Update term sheet data when chips change
  useEffect(() => {
    const canGenerate = checkTermSheetThreshold();
    setState(prev => ({ ...prev, canGenerateTermSheet: canGenerate }));
    
    if (canGenerate) {
      const termSheetData = generateTermSheetData();
      setState(prev => ({ ...prev, termSheetData }));
    }
  }, [state.chips, state.completedCategories, checkTermSheetThreshold, generateTermSheetData]);

  return {
    state,
    updateChip,
    removeChip,
    addChip,
    updateChips,
    getChipsByCategory,
    getAvailableCategoriesForSelection,
    getCategoryProgress,
    getOverallProgress,
    generateTermSheetData,
    checkTermSheetThreshold
  };
};
