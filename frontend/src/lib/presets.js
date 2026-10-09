export const PRESETS = {
  all: {
    label: 'All Combined',
    text: 'Hi, I am Ravi Kumar. My email is ravi.k@test.com, call me on 9876543210. PAN ABCDE1234F, Aadhaar 2344 5678 9012, credit card 4111 1111 1111 1111.',
  },
  email: { label: 'Email', text: 'Please send the invoice to priya.sharma@test.com urgently.' },
  phone: { label: 'Phone', text: 'Call me back on +91-98765 43210 tomorrow morning.' },
  pan: { label: 'PAN', text: 'My PAN for KYC is BNZPM5678K, please verify.' },
  aadhaar: { label: 'Aadhaar', text: 'Aadhaar number 2344 5678 9012 for address proof.' },
  debit: { label: 'Debit card', text: 'My debit card 5555 5555 5555 4444 for the payment.' },
  credit: { label: 'Credit card', text: 'Charge my credit card 4111 1111 1111 1111 for Rs. 2,500.' },
}

export const TYPE_HELP = {
  EMAIL: 'name@test.com',
  PHONE: '10-digit Indian mobile',
  PAN: 'ABCDE1234F uppercase',
  AADHAAR: '12-digit number',
  CARD: '13–19 digit card, Luhn check',
}

export const LIMITS = [
  'Format-only Aadhaar matching can flag number-like identifiers; strict mode uses Verhoeff checksum.',
  'Lowercase PAN values are not matched (uppercase-only specification).',
  'Phone detection follows the implemented +91 / 6-9 prefix rules.',
  'Card detection needs a valid Luhn checksum; debit vs credit share one CARD type (numbers alone cannot distinguish them). CVV/expiry are out of scope — any 3-digit number is too ambiguous.',
  'Name and regional-language detection are outside this MVP.',
]
