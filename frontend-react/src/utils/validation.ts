export const ALLOWED_EMAIL_DOMAINS = ['norscot.co.uk', 'tees.ac.uk'];

export const validateWorkEmail = (email: string): { isValid: boolean; error: string | null } => {
  if (!email || !email.includes('@')) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  // Basic email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Invalid email format' };
  }

  const domain = email.split('@')[1].toLowerCase();
  if (!ALLOWED_EMAIL_DOMAINS.includes(domain)) {
    return { 
      isValid: false, 
      error: `Email domain not allowed.Please use your work email`
    };
  }

  return { isValid: true, error: null };
};
