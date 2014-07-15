(function() {
  'use strict';
  
  var module = angular.module('communityshare.directives.home', [
  ]);

  module.directive(
    'csAdministratorHome',
     function(Session) {
       return {
         scope: false,
         templateUrl: './static/templates/administrator_home.html',
         controller: 'AdministratorHomeController'
       };
     });

  module.directive(
    'csEducatorHome',
     function(Session) {
       return {
         scope: false,
         templateUrl: './static/templates/educator_home.html',
         controller: 'EducatorHomeController'
       };
     });

  module.directive(
    'csCommunityPartnerHome',
     function(Session) {
       return {
         scope: false,
         templateUrl: './static/templates/community_partner_home.html',
         controller: 'CommunityPartnerHomeController'
       };
     });

  module.directive(
    'csSearchesDisplay',
    function() {
      return {
        scope: {
          'searches': '='
        },
        templateUrl: './static/templates/searches_display.html',
        controller: 'SearchesDisplayController'
      };
    });
  
})();
