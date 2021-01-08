const style = getComputedStyle(document.body);
const theme = {};

theme.primary = style.getPropertyValue('--primary');
theme.secondary = style.getPropertyValue('--secondary');
theme.success = style.getPropertyValue('--success');
theme.info = style.getPropertyValue('--info');
theme.warning = style.getPropertyValue('--warning');
theme.danger = style.getPropertyValue('--danger');
theme.light = style.getPropertyValue('--light');
theme.dark = style.getPropertyValue('--dark');
