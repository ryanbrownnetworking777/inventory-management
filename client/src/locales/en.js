export default {
  // Navigation
  nav: {
    overview: 'Overview',
    inventory: 'Inventory',
    orders: 'Orders',
    finance: 'Finance',
    demandForecast: 'Demand Forecast',
    restocking: 'Restocking',
    backlog: 'Backlog',
    reports: 'Reports',
    companyName: 'Catalyst Components',
    subtitle: 'Inventory Management System'
  },

  // Dashboard
  dashboard: {
    title: 'Overview',
    kpi: {
      title: 'Key Performance Indicators',
      inventoryTurnover: 'Inventory Turnover Rate',
      ordersFulfilled: 'Orders Fulfilled',
      orderFillRate: 'Order Fill Rate',
      revenue: 'Revenue (Orders)',
      revenueYTD: 'Revenue (Orders) YTD',
      revenueMTD: 'Revenue (Orders) MTD',
      avgProcessingTime: 'Avg Processing Time (Days)',
      goal: 'Goal'
    },
    summary: {
      title: 'Summary'
    },
    orderHealth: {
      title: 'Order Health',
      totalOrders: 'Total Orders',
      revenue: 'Revenue',
      avgOrderValue: 'Avg Order Value',
      onTimeRate: 'On-Time Rate',
      avgFulfillmentDays: 'Avg Fulfillment (Days)',
      total: 'Total'
    },
    ordersByMonth: {
      title: 'Orders by Month'
    },
    inventoryValue: {
      title: 'Inventory Value by Category'
    },
    inventoryShortages: {
      title: 'Inventory Shortages',
      noShortages: 'No inventory shortages - all orders can be fulfilled!',
      noData: 'No inventory data for selected filters',
      orderId: 'Order ID',
      sku: 'SKU',
      itemName: 'Item Name',
      quantityNeeded: 'Quantity Needed',
      quantityAvailable: 'Quantity Available',
      shortage: 'Shortage',
      daysDelayed: 'Days Delayed',
      priority: 'Priority',
      unitsShort: 'units short',
      days: 'days'
    },
    topProducts: {
      title: 'Top Products by Revenue',
      sku: 'SKU',
      product: 'Product',
      category: 'Category',
      warehouse: 'Warehouse',
      stockStatus: 'Stock Status',
      revenue: 'Revenue',
      unitsOrdered: 'Units Ordered',
      firstOrder: 'First Order',
      inStock: 'In Stock',
      lowStock: 'Low Stock'
    }
  },

  // Inventory
  inventory: {
    title: 'Inventory',
    description: 'Track and manage all inventory items',
    stockLevels: 'Stock Levels',
    skus: 'SKUs',
    searchPlaceholder: 'Search by item name...',
    clearSearch: 'Clear search',
    totalItems: 'Total Items',
    totalValue: 'Total Value',
    lowStockItems: 'Low Stock Items',
    warehouses: 'Warehouses',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      name: 'Name',
      category: 'Category',
      warehouse: 'Warehouse',
      quantity: 'Quantity',
      quantityOnHand: 'Quantity on Hand',
      reorderPoint: 'Reorder Point',
      unitCost: 'Unit Cost',
      unitPrice: 'Unit Price',
      totalValue: 'Total Value',
      location: 'Location',
      status: 'Status'
    }
  },

  // Orders
  orders: {
    title: 'Orders',
    description: 'View and manage customer orders',
    allOrders: 'All Orders',
    totalOrders: 'Total Orders',
    totalRevenue: 'Total Revenue',
    avgOrderValue: 'Avg Order Value',
    onTimeDelivery: 'On-Time Delivery',
    itemsCount: '{count} items',
    quantity: 'Qty',
    submittedOrders: 'Submitted Orders',
    noSubmittedOrders: 'No submitted restock orders yet.',
    submittedOrdersError: 'Failed to load submitted orders',
    loadError: 'Failed to load orders',
    leadTimeValue: '{days} days',
    table: {
      orderNumber: 'Order Number',
      leadTime: 'Lead Time',
      orderId: 'Order ID',
      orderDate: 'Order Date',
      date: 'Date',
      customer: 'Customer',
      category: 'Category',
      warehouse: 'Warehouse',
      items: 'Items',
      value: 'Value',
      totalValue: 'Total Value',
      status: 'Status',
      expectedDelivery: 'Expected Delivery',
      actualDelivery: 'Actual Delivery'
    }
  },

  // Finance/Spending
  finance: {
    title: 'Finance Dashboard',
    description: 'Track revenue, costs, and financial performance',
    totalRevenue: 'Total Revenue',
    totalCosts: 'Total Costs',
    netProfit: 'Net Profit',
    avgOrderValue: 'Avg Order Value',
    fromOrders: 'From {count} orders',
    costBreakdown: 'Procurement + Operational + Labor + Overhead',
    margin: 'margin',
    perOrderRevenue: 'Per order revenue',
    revenueVsCosts: {
      title: 'Monthly Revenue vs Costs',
      revenue: 'Revenue',
      costs: 'Total Costs'
    },
    monthlyCostFlow: {
      title: 'Monthly Cost Flow',
      procurement: 'Procurement',
      operational: 'Operational',
      labor: 'Labor',
      overhead: 'Overhead'
    },
    categorySpending: {
      title: 'Spending by Category',
      ofTotal: 'of total'
    },
    transactions: {
      title: 'Recent Transactions',
      id: 'ID',
      description: 'Description',
      vendor: 'Vendor',
      date: 'Date',
      amount: 'Amount'
    }
  },

  // Demand Forecast
  demand: {
    title: 'Demand Forecast',
    description: 'Analyze demand trends and forecasts',
    increasingDemand: 'Increasing Demand',
    stableDemand: 'Stable Demand',
    decreasingDemand: 'Decreasing Demand',
    itemsCount: '{count} items',
    more: 'more...',
    demandForecasts: 'Demand Forecasts',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      currentDemand: 'Current Demand',
      forecastedDemand: 'Forecasted Demand',
      change: 'Change',
      trend: 'Trend',
      period: 'Period'
    }
  },

  // Restocking
  restocking: {
    title: 'Restocking',
    description: 'Plan restock orders from demand forecasts within your budget',
    budget: 'Budget',
    budgetLabel: 'Restocking Budget',
    budgetHint: 'Adjust the budget to update recommendations. Items with the largest forecasted demand growth are prioritized.',
    recommendedTotal: 'Recommended Total',
    remainingBudget: 'Remaining Budget',
    itemCount: 'Items',
    recommendations: 'Recommended Items',
    updating: 'Updating...',
    noItems: 'No items fit within the current budget. Increase the budget to see recommendations.',
    noCandidates: 'No items currently require restocking.',
    placeOrder: 'Place Order',
    submitting: 'Submitting...',
    orderSuccess: 'Order {orderNumber} has been submitted.',
    viewOrders: 'View in Orders',
    loadError: 'Failed to load restocking recommendations',
    orderError: 'Failed to place the order. Please try again.',
    partial: 'Partial',
    partialNote: 'Partial: the remaining budget only covers part of the recommended quantity for this item. Shown as ordered / recommended.',
    orderPlacedHint: 'Adjust the budget to prepare another order.',
    leadTimeValue: '{days} days',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      trend: 'Trend',
      demand: 'Demand (Current / Forecast)',
      quantity: 'Order Qty',
      unitCost: 'Unit Cost',
      subtotal: 'Subtotal',
      leadTime: 'Lead Time'
    }
  },

  // Filters
  filters: {
    timePeriod: 'Time Period',
    location: 'Location',
    category: 'Category',
    orderStatus: 'Order Status',
    all: 'All',
    allMonths: 'All Months'
  },

  // Statuses
  status: {
    delivered: 'Delivered',
    shipped: 'Shipped',
    processing: 'Processing',
    backordered: 'Backordered',
    inStock: 'In Stock',
    lowStock: 'Low Stock',
    adequate: 'Adequate',
    submitted: 'Submitted'
  },

  // Trends
  trends: {
    increasing: 'increasing',
    stable: 'stable',
    decreasing: 'decreasing'
  },

  // Priority
  priority: {
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  },

  // Categories
  categories: {
    circuitBoards: 'Circuit Boards',
    sensors: 'Sensors',
    actuators: 'Actuators',
    controllers: 'Controllers',
    powerSupplies: 'Power Supplies'
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: 'Raw Materials',
    components: 'Components',
    equipment: 'Equipment',
    consumables: 'Consumables'
  },

  // Warehouses
  warehouses: {
    sanFrancisco: 'San Francisco',
    london: 'London',
    tokyo: 'Tokyo'
  },

  // Months
  months: {
    jan: 'Jan',
    feb: 'Feb',
    mar: 'Mar',
    apr: 'Apr',
    may: 'May',
    jun: 'Jun',
    jul: 'Jul',
    aug: 'Aug',
    sep: 'Sep',
    oct: 'Oct',
    nov: 'Nov',
    dec: 'Dec',
    january: 'January',
    february: 'February',
    march: 'March',
    april: 'April',
    june: 'June',
    july: 'July',
    august: 'August',
    september: 'September',
    october: 'October',
    november: 'November',
    december: 'December'
  },

  // Reports
  reports: {
    title: 'Performance Reports',
    description: 'View quarterly performance metrics and monthly trends',
    quarterlyPerformance: 'Quarterly Performance',
    monthlyRevenueTrend: 'Monthly Revenue Trend',
    monthOverMonth: 'Month-over-Month Analysis',
    quarterLabel: 'Q{quarter} {year}',
    notAvailable: 'N/A',
    noData: 'No orders match the selected filters',
    loadError: 'Failed to load reports',
    table: {
      quarter: 'Quarter',
      totalOrders: 'Total Orders',
      totalRevenue: 'Total Revenue',
      avgOrderValue: 'Avg Order Value',
      fulfillmentRate: 'Fulfillment Rate',
      month: 'Month',
      orders: 'Orders',
      revenue: 'Revenue',
      change: 'Change',
      growthRate: 'Growth Rate'
    },
    stats: {
      totalRevenue: 'Total Revenue',
      avgMonthlyRevenue: 'Avg Monthly Revenue',
      totalOrders: 'Total Orders',
      bestQuarter: 'Best Performing Quarter'
    }
  },

  // Profile Menu
  profile: {
    profileDetails: 'Profile Details',
    myTasks: 'My Tasks',
    logout: 'Logout'
  },

  // Profile Details Modal
  profileDetails: {
    title: 'Profile Details',
    email: 'Email',
    department: 'Department',
    location: 'Location',
    phone: 'Phone',
    joinDate: 'Join Date',
    employeeId: 'Employee ID',
    close: 'Close'
  },

  // Tasks Modal
  tasks: {
    title: 'My Tasks',
    taskTitle: 'Task Title',
    taskTitlePlaceholder: 'Enter task title...',
    priority: 'Priority',
    dueDate: 'Due Date',
    addTask: 'Add Task',
    noTasks: 'No tasks yet. Add your first task above!'
  },

  // Purchase Orders
  purchaseOrder: {
    createButton: 'Create PO',
    viewButton: 'View PO',
    actions: 'Actions',
    createTitle: 'Create Purchase Order',
    viewTitle: 'Purchase Order Details',
    orderId: 'Order ID',
    shortage: 'Shortage',
    units: 'units',
    supplierName: 'Supplier Name',
    supplierPlaceholder: 'Enter supplier name...',
    quantity: 'Quantity',
    unitCost: 'Unit Cost',
    unitCostUsd: 'Unit Cost (USD)',
    expectedDelivery: 'Expected Delivery',
    notes: 'Notes',
    notesPlaceholder: 'Optional notes for this order...',
    noNotes: 'No notes',
    totalCost: 'Total Cost',
    poId: 'PO Number',
    status: 'Status',
    createdDate: 'Created Date',
    submit: 'Create Purchase Order',
    submitting: 'Creating...',
    statuses: {
      pending: 'Pending',
      ordered: 'Ordered',
      shipped: 'Shipped',
      received: 'Received',
      delivered: 'Delivered',
      cancelled: 'Cancelled'
    },
    errors: {
      supplierRequired: 'Supplier name is required.',
      quantityInvalid: 'Quantity must be a whole number of at least 1.',
      unitCostInvalid: 'Unit cost must be greater than 0.',
      deliveryRequired: 'Expected delivery date is required.',
      deliveryInvalid: 'Enter a valid date.',
      deliveryPast: 'Expected delivery date cannot be in the past.',
      createFailed: 'Failed to create purchase order',
      loadFailed: 'Failed to load purchase order.',
      notFound: 'No purchase order was found for this backlog item.'
    }
  },

  // Backlog
  backlog: {
    title: 'Backlog Management',
    description: 'Track and resolve inventory shortages',
    loading: 'Loading backlog...',
    loadError: 'Failed to load backlog: {message}',
    highPriority: 'High Priority',
    mediumPriority: 'Medium Priority',
    lowPriority: 'Low Priority',
    totalItems: 'Total Backlog Items',
    items: 'Backlog Items',
    noItems: 'No backlog items - all orders can be fulfilled!',
    unitsShort: '{count} units short',
    daysCount: '{count} days',
    table: {
      orderId: 'Order ID',
      sku: 'SKU',
      itemName: 'Item Name',
      quantityNeeded: 'Quantity Needed',
      quantityAvailable: 'Quantity Available',
      shortage: 'Shortage',
      daysDelayed: 'Days Delayed',
      priority: 'Priority'
    }
  },

  // Language
  theme: {
    switchToDark: 'Switch to dark mode',
    switchToLight: 'Switch to light mode'
  },

  language: {
    english: 'English',
    japanese: 'Japanese',
    selectLanguage: 'Select Language'
  },

  // Common
  common: {
    loading: 'Loading...',
    error: 'Error',
    noData: 'No data available',
    viewDetails: 'View Details',
    close: 'Close',
    save: 'Save',
    cancel: 'Cancel',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    items: 'items'
  }
}
