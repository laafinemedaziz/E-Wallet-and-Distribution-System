import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID
import requests

class StoreController(http.Controller):

    @http.route('/api/addCourse', type='http', auth='none', method=['POST'], csrf=False, cors="*")
    def addCourse(self):        
        course_data = request.httprequest.get_json()
        response_data = request.env['product.template'].with_user(SUPERUSER_ID).createNewProduct(course_data)
        return (Response(json.dumps(response_data),content_type='application/json'))
    

    @http.route('/api/getCourses', type='http', auth='user', method=['GET'], csrf=False, cors="*")
    def getCourses(self): 
        user = request.env.user        
        courses_data = request.env['product.template'].with_user(SUPERUSER_ID).getAllProducts(user)
        return (Response(json.dumps(courses_data),content_type='application/json'))
    
    @http.route('/api/purchaseCourse', type='http', auth='user', methods=['GET'], csrf=False, cors="*")
    def purchase_course(self):
        course_id = request.params.get("courseId")
        if not course_id:
            return {"error": "Missing 'course_id' parameter"}
        user = request.env.user
        purchase = request.env['course.purchase'].with_user(SUPERUSER_ID).purchaseCourceFlow(course_id, user)
        return (Response(json.dumps({"success": True, "data": purchase}),content_type='application/json'))

       