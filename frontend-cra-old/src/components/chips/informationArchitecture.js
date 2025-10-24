/**
 * Information Architecture for Chip-Based Term Sheet Collection
 * Based on WSGR ContractExpress system and industry standards
 */

// Basic Company Information
export const basicCompanyChips = [
  {
    id: 'company_name',
    category: 'basic_company',
    label: 'Company Name',
    value: '',
    status: 'required',
    type: 'text',
    description: 'Legal name of the company',
    placeholder: 'e.g., TechCorp Inc.',
    validation: { required: true }
  },
  {
    id: 'jurisdiction',
    category: 'basic_company',
    label: 'Jurisdiction',
    value: '',
    status: 'required',
    type: 'select',
    description: 'State or country of incorporation',
    options: [
      'Delaware, USA',
      'California, USA',
      'New York, USA',
      'Singapore',
      'United Kingdom',
      'Cayman Islands',
      'Other'
    ],
    validation: { required: true }
  },
  {
    id: 'business_description',
    category: 'basic_company',
    label: 'Business Description',
    value: '',
    status: 'required',
    type: 'text',
    description: 'Brief description of the company\'s business',
    placeholder: 'e.g., SaaS platform for small businesses',
    validation: { required: true }
  },
  {
    id: 'industry',
    category: 'basic_company',
    label: 'Industry',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Primary industry classification',
    options: [
      'Technology/SaaS',
      'Healthcare',
      'Fintech',
      'E-commerce',
      'Biotech',
      'Clean Tech',
      'Other'
    ],
    validation: { required: true }
  }
];

// Securities & Offering Information
export const securitiesChips = [
  {
    id: 'security_type',
    category: 'securities',
    label: 'Security Type',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Type of securities being issued',
    options: [
      'Series A Preferred Stock',
      'Series B Preferred Stock',
      'Series C Preferred Stock',
      'Seed Preferred Stock',
      'Common Stock',
      'Convertible Notes',
      'SAFE'
    ],
    validation: { required: true }
  },
  {
    id: 'total_shares',
    category: 'securities',
    label: 'Total Shares',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Total number of shares to be issued',
    placeholder: 'e.g., 1,000,000',
    validation: { required: true, min: 1 }
  },
  {
    id: 'price_per_share',
    category: 'securities',
    label: 'Price per Share',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Price per share in USD',
    placeholder: 'e.g., 10.00',
    validation: { required: true, min: 0.01 }
  },
  {
    id: 'offering_size',
    category: 'securities',
    label: 'Total Offering Size',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Total amount being raised',
    placeholder: 'e.g., 5,000,000',
    validation: { required: true, min: 1000 }
  },
  {
    id: 'pre_money_valuation',
    category: 'securities',
    label: 'Pre-money Valuation',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Company valuation before investment',
    placeholder: 'e.g., 20,000,000',
    validation: { required: true, min: 1000 }
  }
];

// Investor Information
export const investorChips = [
  {
    id: 'lead_investor',
    category: 'investors',
    label: 'Lead Investor',
    value: '',
    status: 'required',
    type: 'text',
    description: 'Name of the lead investor',
    placeholder: 'e.g., Sequoia Capital',
    validation: { required: true }
  },
  {
    id: 'investor_type',
    category: 'investors',
    label: 'Investor Type',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Type of lead investor',
    options: [
      'Venture Capital Fund',
      'Private Equity Fund',
      'Angel Investor',
      'Corporate VC',
      'Family Office',
      'Other'
    ],
    validation: { required: true }
  },
  {
    id: 'investment_amount',
    category: 'investors',
    label: 'Investment Amount',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Amount being invested by lead investor',
    placeholder: 'e.g., 3,000,000',
    validation: { required: true, min: 1000 }
  },
  {
    id: 'ownership_percentage',
    category: 'investors',
    label: 'Ownership Percentage',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Percentage ownership after investment',
    placeholder: 'e.g., 15',
    validation: { required: true, min: 0.1, max: 100 }
  },
  {
    id: 'board_seats',
    category: 'investors',
    label: 'Board Seats',
    value: '',
    status: 'required',
    type: 'number',
    description: 'Number of board seats for investor',
    placeholder: 'e.g., 1',
    validation: { required: true, min: 0, max: 5 }
  }
];

// Key Terms - Liquidation Preference
export const liquidationPreferenceChips = [
  {
    id: 'liquidation_multiple',
    category: 'liquidation_preference',
    label: 'Liquidation Multiple',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Multiple of investment for liquidation preference',
    options: ['1x', '1.5x', '2x', '3x', 'Other'],
    validation: { required: true }
  },
  {
    id: 'liquidation_participating',
    category: 'liquidation_preference',
    label: 'Participating Preference',
    value: '',
    status: 'required',
    type: 'boolean',
    description: 'Whether liquidation preference is participating',
    validation: { required: true }
  },
  {
    id: 'liquidation_cap',
    category: 'liquidation_preference',
    label: 'Participation Cap',
    value: '',
    status: 'optional',
    type: 'number',
    description: 'Cap on participation (if applicable)',
    placeholder: 'e.g., 3x',
    dependencies: ['liquidation_participating']
  }
];

// Key Terms - Anti-dilution
export const antiDilutionChips = [
  {
    id: 'anti_dilution_type',
    category: 'anti_dilution',
    label: 'Anti-dilution Protection',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Type of anti-dilution protection',
    options: [
      'None',
      'Weighted Average (Broad-based)',
      'Weighted Average (Narrow-based)',
      'Full Ratchet'
    ],
    validation: { required: true }
  },
  {
    id: 'anti_dilution_exceptions',
    category: 'anti_dilution',
    label: 'Anti-dilution Exceptions',
    value: '',
    status: 'optional',
    type: 'text',
    description: 'Exceptions to anti-dilution protection',
    placeholder: 'e.g., employee stock options, warrants',
    dependencies: ['anti_dilution_type']
  }
];

// Key Terms - Vesting
export const vestingChips = [
  {
    id: 'founder_vesting_period',
    category: 'vesting',
    label: 'Founder Vesting Period',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Vesting period for founder shares',
    options: ['3 years', '4 years', '5 years'],
    validation: { required: true }
  },
  {
    id: 'founder_vesting_cliff',
    category: 'vesting',
    label: 'Founder Vesting Cliff',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Cliff period for founder vesting',
    options: ['No cliff', '6 months', '12 months', '18 months'],
    validation: { required: true }
  },
  {
    id: 'employee_vesting_period',
    category: 'vesting',
    label: 'Employee Vesting Period',
    value: '',
    status: 'required',
    type: 'select',
    description: 'Vesting period for employee stock options',
    options: ['3 years', '4 years', '5 years'],
    validation: { required: true }
  }
];

// Registration Rights
export const registrationRightsChips = [
  {
    id: 'demand_registration',
    category: 'registration_rights',
    label: 'Demand Registration Rights',
    value: '',
    status: 'required',
    type: 'boolean',
    description: 'Right to demand registration of shares',
    validation: { required: true }
  },
  {
    id: 'piggyback_registration',
    category: 'registration_rights',
    label: 'Piggyback Registration Rights',
    value: '',
    status: 'required',
    type: 'boolean',
    description: 'Right to piggyback on company registrations',
    validation: { required: true }
  },
  {
    id: 's3_registration',
    category: 'registration_rights',
    label: 'S-3 Registration Rights',
    value: '',
    status: 'optional',
    type: 'boolean',
    description: 'Right to use S-3 registration statements'
  }
];

// All Categories
export const chipCategories = [
  {
    id: 'basic_company',
    name: 'Basic Company Information',
    description: 'Core company details and jurisdiction',
    icon: 'Building2',
    color: 'blue',
    chips: basicCompanyChips,
    order: 1
  },
  {
    id: 'securities',
    name: 'Securities & Offering',
    description: 'Details about the securities being issued',
    icon: 'DollarSign',
    color: 'green',
    chips: securitiesChips,
    dependencies: ['basic_company'],
    order: 2
  },
  {
    id: 'investors',
    name: 'Investor Information',
    description: 'Lead investor and investment details',
    icon: 'Users',
    color: 'purple',
    chips: investorChips,
    dependencies: ['basic_company'],
    order: 3
  },
  {
    id: 'liquidation_preference',
    name: 'Liquidation Preference',
    description: 'Liquidation preference terms',
    icon: 'Shield',
    color: 'red',
    chips: liquidationPreferenceChips,
    dependencies: ['securities', 'investors'],
    order: 4
  },
  {
    id: 'anti_dilution',
    name: 'Anti-dilution Protection',
    description: 'Anti-dilution protection terms',
    icon: 'Lock',
    color: 'orange',
    chips: antiDilutionChips,
    dependencies: ['securities'],
    order: 5
  },
  {
    id: 'vesting',
    name: 'Stock Vesting',
    description: 'Vesting schedules for founders and employees',
    icon: 'Clock',
    color: 'indigo',
    chips: vestingChips,
    dependencies: ['basic_company'],
    order: 6
  },
  {
    id: 'registration_rights',
    name: 'Registration Rights',
    description: 'Registration rights for investors',
    icon: 'FileText',
    color: 'teal',
    chips: registrationRightsChips,
    dependencies: ['investors'],
    order: 7
  }
];

// Term Sheet Generation Threshold
export const termSheetThreshold = {
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

// Helper function to get all chips
export const getAllChips = () => {
  return chipCategories.flatMap(category => category.chips);
};

// Helper function to get chips by category
export const getChipsByCategory = (categoryId) => {
  const category = chipCategories.find(cat => cat.id === categoryId);
  return category ? category.chips : [];
};

// Helper function to get available categories based on dependencies
export const getAvailableCategories = (completedCategories) => {
  return chipCategories.filter(category => {
    if (!category.dependencies) return true;
    return category.dependencies.every(dep => completedCategories.includes(dep));
  });
};
