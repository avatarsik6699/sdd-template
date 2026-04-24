export default defineNuxtPlugin((nuxtApp) => {
  document.documentElement.dataset.appReady = 'false';

  const markReady = () => {
    document.documentElement.dataset.appReady = 'true';
  };

  nuxtApp.hook('app:suspense:resolve', markReady);
  nuxtApp.hook('page:finish', markReady);
  nuxtApp.hook('page:loading:start', () => {
    document.documentElement.dataset.appReady = 'false';
  });
});
