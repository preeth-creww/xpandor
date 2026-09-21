// Global site constants for Xpandor.net
export const SITE_TITLE = 'Xpandor | Retail Expansion Partner';
export const SITE_DESCRIPTION = 'Xpandor takes ownership of the operational complexity behind physical expansion. Locations, fit-outs, signage, and retail staffing across Bengaluru and South India.';

export const CONTACT_PHONE = '+91 98458 08425';
export const CONTACT_EMAIL = 'preetham@xpandor.net';
export const WHATSAPP_NUMBER = '919845808425';
export const WHATSAPP_BASE_URL = 'https://wa.me/919845808425';
export const FOUNDER_NAME = 'Preetham Phirangi';
export const FOUNDER_ROLE = 'Founder & Expansion Lead';
export const FOUNDER_LINKEDIN = 'https://www.linkedin.com/in/preetham-phirangi';

export function getWhatsAppExpansionUrl(details?: {
	brand?: string;
	city?: string;
	sqft?: string;
	service?: string;
}) {
	let text = "Hi Preetham, I'd like to discuss a retail expansion plan with Xpandor.";
	if (details?.brand) {
		text += ` Brand: ${details.brand}.`;
	}
	if (details?.city) {
		text += ` Target Market: ${details.city}.`;
	}
	if (details?.sqft) {
		text += ` Store Size: ${details.sqft}.`;
	}
	if (details?.service) {
		text += ` Scope: ${details.service}.`;
	}
	return `${WHATSAPP_BASE_URL}?text=${encodeURIComponent(text)}`;
}
