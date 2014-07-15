(function() {
  'use strict';

  var module = angular.module(
    'communityshare.controllers.authentication',
    [
      'communityshare.services.authentication',
    ]);
  
  module.controller(
    'ResetPasswordController',
    function($scope, Authenticator, $routeParams, $location) {
      var key = $routeParams.key;
      $scope.password = '';
      $scope.repeat_password = '';
      $scope.successfulReset = false;
      $scope.failedReset = false;
      // passwordMethods is used for communication between password and
      // password_repeat directives.
      $scope.passwordMethods = {};
      $scope.resetPassword = function() {
        var promise = Authenticator.resetPassword(key, $scope.password);
        promise.then(
          function() {
            $location.path('/login').search({});
            $scope.successfulReset = true;
          },
          function(message) {
            $scope.errorMessage = message;
          });
      };
    });

  module.controller(
    'RequestResetPasswordController',
    function($scope, Authenticator) {
      $scope.email = '';
      $scope.successfulRequest = false;
      $scope.failedRequest = false;
      $scope.requestResetPassword = function() {
        var promise = Authenticator.requestResetPassword($scope.email);
        promise.then(
          function() {
            $scope.successfulRequest = true;
            $scope.errorMessage = '';
          },
          function(message) {
            $scope.successfulRequest = false;
            var msg = 'Failed to reset password';
            if (message) {
              if (message == 'Not found') {
                msg += ': ' + 'Unknown email address';
              } else {
                msg += ': ' + message;
              }
            }
            $scope.errorMessage = msg;
          });
      };
    });

  module.controller(
    'ConfirmEmailController',
    function($scope, Authenticator, $routeParams, $location) {
      var key = $routeParams.key;
      $scope.confirmed = false;
      $scope.failedReset = false;
      var promise = Authenticator.confirmEmail(key);
      promise.then(
        function(user) {
          $scope.confirmed = true;
        },
        function(message) {
          $scope.errorMessage = message;
        });
    });

  module.controller(
    'LogoutController',
    function(Authenticator, Session) {
      Authenticator.clean();
      Session.activeUser = undefined;
    });

  module.controller(
    'DefaultController',
    function($scope, user, $location) {
      if (user) {
        $location.path('home');
      }
    });

  module.controller(
    'LoginController',
    function($scope, $location, Authenticator) {
      var nextLocation = $location.search().goto;
      $scope.email = undefined;
      $scope.password = undefined;
      $scope.errorMessage = '';
      $scope.login = function() {
        var userPromise = Authenticator.authenticateWithEmailAndPassword(
          $scope.email, $scope.password);
        userPromise.then(
          function(user) {
            if (nextLocation) {
              $location.path(nextLocation);
            } else {
              $location.path("/home");
            }
          },
          function(message) {
            var msg = '';
            if (message) {
              msg = ': ' + message;
            }
            $scope.errorMessage = 'Authentication failed' + msg;
          }
        );
      };
    });

  module.controller(
    'NavigationController',
    function($scope, Session) {
      $scope.Session = Session;
    });
  
  module.controller(
    'DropdownCtrl',
    function($scope) {
      $scope.items = [
        "Find Project",
        "Create Project",
        "Update Project"
      ];
    });

})();
