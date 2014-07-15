(function() {
  'use strict';
  
  var module = angular.module('communityshare.directives.mainview', [
    'ui.bootstrap.alert'
  ]);

  module.directive(
    'csUserAgreement',
    function() {
      return {
        templateUrl: '/static/templates/user_agreement.html'
      };
    });

  module.directive(
    'csForbidden',
    function() {
      return {
        templateUrl: '/static/templates/forbidden.html'
      };
    });

  module.directive(
    'csDatepicker',
    function() {
      return {
        scope: {
          'ngModel': '='
        },
        templateUrl: '/static/templates/datepicker.html',
        controller: function($scope) {

          $scope.today = function() {
            $scope.ngModel = new Date();
          };

          $scope.clear = function () {
            $scope.ngModel = null;
          };

          $scope.minDate = new Date();
          $scope.maxDate = new Date();
          $scope.maxDate.setFullYear($scope.maxDate.getFullYear()+1);
          
          $scope.open = function($event) {
            $event.preventDefault();
            $event.stopPropagation();
            $scope.opened = true;
          };

          $scope.dateOptions = {
            formatYear: 'yy',
            startingDay: 1
          };
        }
      };
    });

})();
