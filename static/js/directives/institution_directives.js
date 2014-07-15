(function() {
  'use strict';
  
  var module = angular.module('communityshare.directives.institutions', [
    'communityshare.services.user'
  ]);

  module.directive(
    'csInstitutions',
     function(Session, Institution) {
       return {
         scope: {
           user: '=',
           isEducator: '=',
           isCommunityPartner: '='
         },
         templateUrl: './static/templates/institution_adder.html',
         controller: function($scope) {
           // FIXME: Not scaleable.  Change to get the most popular.
           var institutionsPromise = Institution.get_many();
           var institutionTypes = [];
           $scope.options = {institutions: [],
                             institutionTypes: [],
                            };
           if ($scope.isCommunityPartner) {
             $scope.options.institutionTypes = [
               'Company', 'University', 'School'];
           } else if ($scope.isEducator) {
             $scope.options.institutionTypes = [
               'University', 'Public School', 'Charter School', 'Private School'];
           }
           if ($scope.user.institution_associations.length === 0) {
             $scope.user.institution_associations.push({});
           }
           institutionsPromise.then(
             function(institutions) {
               $scope.options.institutions = institutions;
             });
         }
       };
     });

  module.directive(
    'csInstitutionAssociationEdit',
    function() {
      return {
        scope: {
          institutionAssociation: '=',
          institutions: '=',
          institutionTypes: '=',
          methods: '=',
          index: '@'
        },
        templateUrl: 'static/templates/institution_association.html'
      };
    });
  
})();
